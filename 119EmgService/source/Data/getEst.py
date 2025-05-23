import time
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json
import os

# =====================
# 1. 설정
# =====================
API_KEY = "28c046f4a78799253e8402cf498ff472"
HEADERS = {"Authorization": f"KakaoAK {API_KEY}"}
EST_FILE = '다중이용업소 현황.csv'
GRID_FILE = 'tempDataset.csv'
OUTPUT_FILE = 'grid_est_counts.csv'
CACHE_FILE = 'geocode_cache.json'

# =====================
# 2. 캐시 로드
# =====================
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
else:
    cache = {}

# =====================
# 3. 데이터 로드
# =====================
df_est = pd.read_csv(EST_FILE, encoding='utf-8')
cols = df_est.columns
lon_col = next((c for c in cols if '경도' in c or c.lower()=='lon'), None)
lat_col = next((c for c in cols if '위도' in c or c.lower()=='lat'), None)
address_col = next((c for c in cols if '도로명' in c or '지번' in c), None)
buld_col = next((c for c in cols if 'buld_nm' in c.lower()), None)
road_col = next((c for c in cols if 'road_nm' in c.lower()), None)

df_grid = pd.read_csv(GRID_FILE, encoding='utf-8')

# =====================
# 4. 좌표 확보 함수
# =====================
def geocode(raw_query, call_counter):
    if not raw_query or pd.isna(raw_query):
        return None, None, call_counter
    key = str(raw_query)
    if key in cache:
        return cache[key][0], cache[key][1], call_counter
    x = y = None
    for q in (key, f"서울 {key}"):
        try:
            resp = requests.get(
                'https://dapi.kakao.com/v2/local/search/keyword.json',
                headers=HEADERS,
                params={'query': q},
                timeout=5
            )
            call_counter += 1
            if resp.status_code == 200:
                docs = resp.json().get('documents', [])
                if docs:
                    x = float(docs[0]['x'])
                    y = float(docs[0]['y'])
                    break
        except:
            pass
        time.sleep(0.2)
        if call_counter % 100 == 0:
            print(f"API 호출 횟수: {call_counter}")
    cache[key] = [x, y]
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    return x, y, call_counter

# =====================
# 5. 업소 위치 확보
# =====================
if lon_col and lat_col:
    df_est['lon'] = df_est[lon_col]
    df_est['lat'] = df_est[lat_col]
else:
    lons, lats = [], []
    calls = 0
    for _, row in df_est.iterrows():
        x = y = None
        # 1) 업소명 캐시만
        name_key = str(row.get('trgtobj_nm'))
        if name_key in cache:
            x, y = cache[name_key]
        # 2) 건물명 API
        if x is None and buld_col and pd.notna(row.get(buld_col)):
            x, y, calls = geocode(str(row.get(buld_col)), calls)
        # 3) 도로명주소 API
        if x is None and road_col and pd.notna(row.get(road_col)):
            x, y, calls = geocode(str(row.get(road_col)), calls)
        lons.append(x)
        lats.append(y)
    df_est['lon'] = lons
    df_est['lat'] = lats

df_est = df_est.dropna(subset=['lon', 'lat']).reset_index(drop=True)

# =====================
# 6. GeoDataFrame 변환 및 CRS
# =====================
gdf_est = gpd.GeoDataFrame(
    df_est,
    geometry=gpd.points_from_xy(df_est['lon'], df_est['lat']),
    crs='epsg:4326'
)
gdf_grid = gpd.GeoDataFrame(
    df_grid,
    geometry=gpd.points_from_xy(df_grid['center_lon'], df_grid['center_lat']),
    crs='epsg:4326'
)
gdf_est = gdf_est.to_crs(epsg=5179)
gdf_grid = gdf_grid.to_crs(epsg=5179)

# =====================
# 7. 격자 폴리곤 생성
# =====================
HALF_SIDE = 125  # 250m 격자 반변
gdf_grid['geometry'] = gdf_grid.geometry.buffer(HALF_SIDE, cap_style=3)

# =====================
# 8. 공간 결합 & 집계
# =====================
joined = gpd.sjoin(
    gdf_est,
    gdf_grid[['orig_idx', 'geometry']],
    how='inner',
    predicate='within'
)
counts = joined.groupby('orig_idx').size().reset_index(name='est_count')

df_out = df_grid.merge(counts, on='orig_idx', how='left')
df_out['est_count'] = df_out['est_count'].fillna(0).astype(int)

# =====================
# 9. 저장
# =====================
df_out.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
print(f"저장 완료: {OUTPUT_FILE} (총 업소: {len(df_est)}, 집계된 격자 수: {df_out['est_count'].gt(0).sum()})")
