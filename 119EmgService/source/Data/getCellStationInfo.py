#!/usr/bin/env python3
# coding: utf-8

import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# ───────────────────────────────────────────────────────
# 1) 파일 경로 (스크립트와 같은 디렉토리에 두세요)
GRID_CSV    = 'gridData.csv'
SHAPEFILE   = 'LARD_ADM_SECT_SGG_11_202505.shp'
STATION_CSV = '소방청_시도 소방서 현황_20240630.csv'
CENTER_CSV  = '소방청_119안전센터 현황_20240630.csv'
OUTPUT_CSV  = 'gridNearest119Center.csv'

# ───────────────────────────────────────────────────────
# 2) 원본 격자 읽기 및 Unnamed 컬럼 제거
grid_df = pd.read_csv(GRID_CSV, encoding='utf-8-sig')
grid_df = grid_df.loc[:, ~grid_df.columns.str.startswith('Unnamed')]
grid_df['grid_idx'] = grid_df.index  # 식별자

# ───────────────────────────────────────────────────────
# 3) 행정구역(shapefile) 읽기 & 구명 추출
gu_gdf = gpd.read_file(SHAPEFILE)
gu_gdf = gu_gdf.rename(columns={'SGG_NM':'gu_name'})[['gu_name','geometry']]
# 예: "서울특별시 강서구" → "강서구"
gu_gdf['gu_name'] = gu_gdf['gu_name'].str.split().str[-1]

# CRS 자동 변환 (위경도 → EPSG:5179)
if gu_gdf.crs.is_geographic:
    gu_gdf = gu_gdf.to_crs('EPSG:5179')
metric_crs = gu_gdf.crs

# ───────────────────────────────────────────────────────
# 4) 격자 중심점 및 250×250m 사각형 생성
grid_centers = gpd.GeoDataFrame(
    grid_df,
    geometry=gpd.points_from_xy(grid_df['center_lon'],
                                grid_df['center_lat']),
    crs='EPSG:4326'
).to_crs(metric_crs)

half = 125  # 250m/2
grid_squares = grid_centers.copy()
grid_squares['geometry'] = grid_squares.geometry.apply(
    lambda p: box(p.x-half, p.y-half, p.x+half, p.y+half)
)

# ───────────────────────────────────────────────────────
# 5) 그리드×구 교차(intersection) 후 면적과 비율 계산
overlay = gpd.overlay(grid_squares, gu_gdf, how='intersection')
overlay['intersect_area'] = overlay.area
grid_area = (2*half)**2
overlay['area_pct'] = overlay['intersect_area'] / grid_area

# ───────────────────────────────────────────────────────
# 6) 소방서·119안전센터 데이터 읽기 & 구명 추출
station = pd.read_csv(STATION_CSV, encoding='cp949')
center  = pd.read_csv(CENTER_CSV,  encoding='cp949')

station['gu_name'] = station['주소'].str.split().str[1]
center ['gu_name'] = center ['주소'].str.split().str[1]

svc_station = station[['gu_name','소방서','주소']].rename(
    columns={'소방서':'service_name',
             '주소':'service_address'}
)
svc_station['service_type'] = '소방서'

svc_center = center[['gu_name','119안전센터명','주소']].rename(
    columns={'119안전센터명':'service_name',
             '주소':'service_address'}
)
svc_center['service_type'] = '119안전센터'

service_df = pd.concat([svc_station, svc_center], ignore_index=True)

# ───────────────────────────────────────────────────────
# 7) 주소 → 위경도 (geocoding)
geolocator = Nominatim(user_agent="grid_locator")
geocode    = RateLimiter(geolocator.geocode, min_delay_seconds=1)

service_df['loc'] = service_df['service_address'].apply(geocode)
service_df['lat'] = service_df['loc'].apply(lambda x: x.latitude  if x else None)
service_df['lon'] = service_df['loc'].apply(lambda x: x.longitude if x else None)

service_gdf = gpd.GeoDataFrame(
    service_df.drop(columns=['loc']),
    geometry=gpd.points_from_xy(service_df['lon'],
                                service_df['lat']),
    crs='EPSG:4326'
).to_crs(metric_crs)

# ───────────────────────────────────────────────────────
# 8) 각 교차영역(row)에 가장 가까운 기관 찾기
grid_center_lookup = dict(zip(grid_centers['grid_idx'],
                              grid_centers.geometry))

def find_nearest(row):
    cands = service_gdf[service_gdf['gu_name']==row['gu_name']]
    if cands.empty:
        return pd.Series({'service_name':None,
                          'service_address':None,
                          'service_type':None})
    center_pt = grid_center_lookup[row['grid_idx']]
    dists = cands.geometry.distance(center_pt)
    nearest = cands.iloc[dists.idxmin()]
    return pd.Series({
        'service_name':    nearest['service_name'],
        'service_address': nearest['service_address'],
        'service_type':    nearest['service_type']
    })

overlay[['service_name','service_address','service_type']] = (
    overlay.apply(find_nearest, axis=1)
)

# ───────────────────────────────────────────────────────
# 9) 한 행(flat)으로 묶기
orig_cols = grid_df.columns.tolist()
agg_map = {c:'first' for c in orig_cols}
agg_map.update({
    'gu_name':         lambda s: ';'.join(s),
    'area_pct':        lambda s: ';'.join(s.round(4).astype(str)),
    'service_name':    lambda s: ';'.join(s),
    'service_address': lambda s: ';'.join(s),
    'service_type':    lambda s: ';'.join(s),
})

flat = overlay.groupby('grid_idx', as_index=False).agg(agg_map)

# 컬럼 순서 재정렬
cols = (
    ['grid_idx'] +
    [c for c in flat.columns
     if c not in ['grid_idx','gu_name','area_pct',
                  'service_name','service_address','service_type']] +
    ['gu_name','area_pct',
     'service_name','service_address','service_type']
)
flat = flat[cols]

# ───────────────────────────────────────────────────────
# 10) 결과 저장
flat.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print("✅ 생성 완료:", OUTPUT_CSV)
