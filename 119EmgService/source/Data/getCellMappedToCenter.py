import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon

# ========================================
# 1) 상수 정의
# ========================================
GRID_SIDE  = 250            # 격자 한 변 (m)
HALF_SIDE  = GRID_SIDE / 2  # 반변 (m)
TARGET_CRS = 'epsg:5179'    # 서울 TM 좌표계

# ========================================
# 2) 격자 데이터 읽기 및 전처리
# ========================================
df_grid = (
    pd.read_csv('gridData.csv', encoding='utf-8')
      .loc[:, lambda df: ~df.columns.str.contains(r'^Unnamed')]
)
df_grid['grid_id'] = df_grid.index

gdf_grid = gpd.GeoDataFrame(
    df_grid,
    geometry=gpd.points_from_xy(df_grid.center_lon, df_grid.center_lat),
    crs='epsg:4326'
).to_crs(TARGET_CRS)

def make_square(pt):
    x, y = pt.x, pt.y
    return Polygon([
        (x - HALF_SIDE, y - HALF_SIDE),
        (x - HALF_SIDE, y + HALF_SIDE),
        (x + HALF_SIDE, y + HALF_SIDE),
        (x + HALF_SIDE, y - HALF_SIDE),
    ])

gdf_grid['cell_geom'] = gdf_grid.geometry.map(make_square)
gdf_grid.set_geometry('cell_geom', inplace=True)

# ========================================
# 3) 구 경계 읽기 및 전처리
# ========================================
gdf_dist = (
    gpd.read_file('LARD_ADM_SECT_SGG_11_202505.shp', encoding='euc-kr')
       .loc[:, lambda df: ~df.columns.str.contains(r'^Unnamed')]
)
gdf_dist = gdf_dist[gdf_dist['SGG_NM'].str.startswith('서울특별시')]
gdf_dist['district'] = (
    gdf_dist['SGG_NM']
      .str.replace(r'^서울특별시\s*', '', regex=True)
      .str.strip()
)
gdf_dist = gdf_dist[['district','geometry']].to_crs(TARGET_CRS)

# ========================================
# 4) 119 서비스 지점 읽기 및 정규화
# ========================================
df_srv = (
    pd.read_csv('119serviceGeocoded.csv', encoding='utf-8')
      .loc[:, lambda df: ~df.columns.str.contains(r'^Unnamed')]
)
# district 컬럼을 '노원구' 형태로 정규화
df_srv['district'] = (
    df_srv['district']
      .str.replace(r'^서울특별시\s*', '', regex=True)
      .str.strip()
)

gdf_srv = gpd.GeoDataFrame(
    df_srv,
    geometry=gpd.points_from_xy(df_srv.longitude, df_srv.latitude),
    crs='epsg:4326'
).to_crs(TARGET_CRS)

# ========================================
# 5) 격자 ↔ 구 교차(intersection) 및 면적 비율 계산
# ========================================
gdf_inter = gpd.overlay(
    gdf_grid[['grid_id','cell_geom']],
    gdf_dist,
    how='intersection'
)
gdf_inter['area_ratio'] = gdf_inter.geometry.area / (GRID_SIDE * GRID_SIDE)

# ========================================
# 6) 각 격자–구별 최단거리 서비스 찾기
# ========================================
records = []
for _, row in gdf_inter.iterrows():
    gid    = row['grid_id']
    distnm = row['district']
    ratio  = row['area_ratio']
    poly   = row.geometry

    cand = gdf_srv[gdf_srv['district'] == distnm].copy()
    if cand.empty:
        continue

    cand['dist'] = cand.geometry.distance(poly)
    nearest = cand.loc[cand['dist'].idxmin()]

    records.append({
        'grid_id'      : gid,
        'district'     : distnm,
        'service_name' : nearest['service_name'],
        'service_lon'  : nearest['longitude'],
        'service_lat'  : nearest['latitude'],
        'area_ratio'   : ratio
    })

df_rec = pd.DataFrame(records)

# ========================================
# 7) grid_id별로 리스트 필드로 묶기
# ========================================
df_grouped = (
    df_rec
      .groupby('grid_id')
      .agg({
          'district'     : lambda x: ';'.join(x),
          'service_name' : lambda x: ';'.join(x),
          'service_lon'  : lambda x: ';'.join(map(str,x)),
          'service_lat'  : lambda x: ';'.join(map(str,x)),
          'area_ratio'   : lambda x: ';'.join(map(str,x)),
      })
      .reset_index()
)

# ========================================
# 8) area_ratio 보정: “단일 서비스+ratio<1” → ratio=1
# ========================================
def fix_ratio(ratio_str, svc_str):
    ratios = ratio_str.split(';')
    services = svc_str.split(';')
    # 서비스가 하나뿐이고 비율<1 이면 1로 교체
    if len(services) == 1 and float(ratios[0]) < 1.0:
        return '1'
    return ratio_str

df_grouped['area_ratio'] = df_grouped.apply(
    lambda r: fix_ratio(r['area_ratio'], r['service_name']),
    axis=1
)

# ========================================
# 9) 원본 격자 정보와 병합 → CSV 저장
# ========================================
df_base = (
    gdf_grid
      .drop(columns=['geometry','cell_geom'])
      .loc[:, lambda df: ~df.columns.str.contains(r'^Unnamed')]
)

df_out = pd.merge(
    df_base,
    df_grouped,
    on='grid_id',
    how='left'
).loc[:, lambda df: ~df.columns.str.contains(r'^Unnamed')]

df_out.to_csv('gridNearest119Center.csv',
              index=False,
              encoding='utf-8-sig')

print("✅ gridNearest119Center.csv 생성 완료 (보정된 area_ratio 적용)")
