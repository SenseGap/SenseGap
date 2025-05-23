#!/usr/bin/env python3
# compute_grid_response_time.py

import pandas as pd
import requests
import time
import re
from pyproj import Transformer
import geopandas as gpd
import fiona
from shapely.geometry import shape, Polygon, Point

# ── 설정 ──
KAKAO_API_KEY       = "28c046f4a78799253e8402cf498ff472"
GRID_CSV            = "gridData.csv"
FIRE_CSV            = "소방청_시도 소방서 현황_20240630.csv"
CENTER_CSV          = "소방청_119안전센터 현황_20240630.csv"
SHAPEFILE_SGG       = "LARD_ADM_SECT_SGG_11_202505.shp"
OUTPUT_CSV          = "grid_to_response_time.csv"

# 구별 관할 소방서 매핑
DISTRICT_TO_STATION = {
    "강남구":"강남소방서", "강동구":"강동소방서", "강북구":"강북소방서",
    "강서구":"강서소방서", "관악구":"관악소방서", "광진구":"광진소방서",
    "구로구":"구로소방서", "노원구":"노원소방서", "도봉구":"도봉소방서",
    "동대문구":"동대문소방서", "동작구":"동작소방서", "마포구":"마포소방서",
    "서대문구":"서대문소방서", "서초구":"서초소방서", "송파구":"송파소방서",
    "양천구":"양천소방서", "영등포구":"영등포소방서", "용산구":"용산소방서",
    "은평구":"은평소방서", "종로구":"종로소방서", "중구":"중부소방서",
    "중랑구":"중랑소방서", "성동구":"성동소방서", "성북구":"성북소방서",
}

# ── 좌표 변환기 ──
to_wgs = Transformer.from_crs("epsg:5181", "epsg:4326", always_xy=True)

# ── 1) 소방서·안전센터 데이터 로드 & Geocode ──
def extract_district(addr):
    m = re.search(r'서울특별시\s+(\S+구)', addr)
    return m.group(1) if m else None

def geocode(addr):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    r = requests.get(url, headers=headers, params={"query": addr})
    r.raise_for_status()
    docs = r.json().get("documents", [])
    if docs:
        return float(docs[0]['x']), float(docs[0]['y'])
    return None, None

_cache = {}
def geocode_cached(addr):
    if addr not in _cache:
        _cache[addr] = geocode(addr)
    return _cache[addr]

# 본소방서
df_fire = pd.read_csv(FIRE_CSV, encoding='cp949')
df_fire = df_fire[df_fire['본부명'].str.contains("서울소방재난본부", na=False)]
df_fire['district'] = df_fire['주소'].map(extract_district)
df_fire[['lon','lat']] = df_fire['주소'].apply(lambda a: pd.Series(geocode_cached(a)))

# 119안전센터
df_center = pd.read_csv(CENTER_CSV, encoding='cp949')
df_center = df_center[df_center['시도본부']=="서울특별시"]
df_center['district'] = df_center['주소'].map(extract_district)
df_center[['lon','lat']] = df_center['주소'].apply(lambda a: pd.Series(geocode_cached(a)))

stations = pd.concat([
    df_fire.rename(columns={'소방서':'name'})[['district','name','lon','lat']],
    df_center.rename(columns={'119안전센터명':'name'})[['district','name','lon','lat']]
], ignore_index=True)

# ── 2) 그리드 셀(250×250m) 생성 ──
df_grid = pd.read_csv(GRID_CSV)
gdf_grid = gpd.GeoDataFrame(
    df_grid,
    geometry=gpd.points_from_xy(df_grid.center_lon, df_grid.center_lat),
    crs="EPSG:4326"
).to_crs(epsg=5181)

half = 125  # meters
def make_cell(pt):
    x, y = pt.x, pt.y
    return Polygon([
        (x-half, y-half), (x+half, y-half),
        (x+half, y+half), (x-half, y+half)
    ])
gdf_grid['geometry'] = gdf_grid['geometry'].apply(make_cell)

# ── 3) Shapefile로부터 서울시 25개 구 경계만 뽑아오기 ──
districts = []
with fiona.open(SHAPEFILE_SGG, 'r') as src:
    shp_crs = src.crs  # EPSG:5186
    for feat in src:
        name_full = feat['properties']['SGG_NM']  # ex: "서울특별시 종로구"
        if not name_full.startswith("서울특별시"):
            continue
        gu = name_full.split()[-1]               # "종로구" 등
        geom = shape(feat['geometry'])
        districts.append({'district': gu, 'geometry': geom})

gdf_districts = gpd.GeoDataFrame(districts, crs=shp_crs).to_crs(epsg=5181)

# ── 4) 셀 × 구 교차면적 계산 → 면적비(weight) 산출 ──
inter = gpd.overlay(gdf_grid, gdf_districts[['district','geometry']], how='intersection')
inter['area']      = inter.geometry.area
total_by_cell      = inter.groupby('i')['area'].sum().rename('cell_area')
inter = inter.join(total_by_cell, on='i')
inter['weight']    = inter['area'] / inter['cell_area']

# ── 5) 카카오 도로시간 API 함수 ──
def get_drive_time(orig, dest):
    url = "https://apis-navi.kakaomobility.com/v1/directions"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "origin":      f"{orig[1]},{orig[0]}",  # lon,lat
        "destination": f"{dest[1]},{dest[0]}",  # lon,lat
        "priority":    "RECOMMEND"
    }
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json()['routes'][0]['summary']['duration']

# ── 6) 셀별 가중 평균 응답시간 계산 ──
# stations도 EPSG:5181로 변환
gdf_st = gpd.GeoDataFrame(
    stations,
    geometry=gpd.points_from_xy(stations.lon, stations.lat),
    crs="EPSG:4326"
).to_crs(epsg=5181)

results = []
for cell_id, grp in inter.groupby('i'):
    # 셀 중심 위경도
    center_pt = gdf_grid[gdf_grid['i']==cell_id].to_crs(epsg=4326).centroid.iloc[0]
    orig = (center_pt.y, center_pt.x)
    total_time = 0.0

    for _, row in grp.iterrows():
        gu      = row['district']
        w       = row['weight']
        main_st = DISTRICT_TO_STATION.get(gu)
        cand    = gdf_st[gdf_st['district']==gu].copy()
        # 본소방서도 후보에 추가
        if main_st:
            cand = pd.concat([cand,
                              cand[cand['name']==main_st]], ignore_index=True)
        times = []
        for _, st in cand.iterrows():
            dest = (st.geometry.y, st.geometry.x)
            try:
                t = get_drive_time(orig, dest)
                times.append(t)
            except:
                pass
        if times:
            total_time += w * min(times)

    results.append({
        'i': cell_id,
        'weighted_travel_time_s': total_time
    })

pd.DataFrame(results) \
  .to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

print(f"완료: {len(results)}개 셀 → {OUTPUT_CSV}")
