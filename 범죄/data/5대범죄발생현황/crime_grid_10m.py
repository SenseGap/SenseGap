import pandas as pd
import numpy as np
import geopandas as gpd
import logging
import folium
from folium.plugins import HeatMap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. 자치구 경계 불러오기 (서울시)
sgg_boundary = gpd.read_file('LARD_ADM_SECT_SGG_11_202505.shp').to_crs(epsg=4326)
sgg_boundary['SGG_NM'] = sgg_boundary['SGG_NM'].str.replace('서울특별시 ', '').str.replace(' ', '')

# 2. 5대범죄 데이터 불러오기 및 전처리
crime_path = '5대범죄발생현황_20250510150209.csv'

# 1. 헤더 4줄 합치기
header = pd.read_csv(crime_path, nrows=4, header=None)
columns = []
for i in range(2, len(header.columns)):
    col_name = f"{header.iloc[2, i]}_{header.iloc[3, i]}"
    columns.append(col_name)
columns = ['구분1', '자치구'] + columns

# 2. 데이터 읽기
df = pd.read_csv(crime_path, skiprows=4, header=None)
df.columns = columns

# 3. 자치구별 소계(발생)만 추출
df = df[df['구분1'] == '합계']
df = df[df['자치구'] != '소계']
df['자치구'] = df['자치구'].str.replace(' ', '')
df['전체'] = pd.to_numeric(df['소계_발생'], errors='coerce').fillna(0)

# 3. 10m 격자 생성 (서울시 전체 범위)
grid_size = 0.00009  # 약 10m
min_lon, min_lat, max_lon, max_lat = sgg_boundary.total_bounds
x_indices = np.arange(min_lon, max_lon, grid_size)
y_indices = np.arange(min_lat, max_lat, grid_size)
grid_points = []
for x in x_indices:
    for y in y_indices:
        grid_points.append({'center_lon': x + grid_size/2, 'center_lat': y + grid_size/2})
grid_gdf = gpd.GeoDataFrame(
    grid_points,
    geometry=gpd.points_from_xy([p['center_lon'] for p in grid_points], [p['center_lat'] for p in grid_points]),
    crs='EPSG:4326'
)

# 4. 격자-자치구 spatial join
grid_sgg = gpd.sjoin(grid_gdf, sgg_boundary, how='inner', predicate='within')

# 5. 자치구별 격자 개수 계산
grid_count = grid_sgg.groupby('SGG_NM').size().reset_index(name='grid_count')

# 6. 범죄 데이터와 격자 개수 merge
crime_df = df.merge(grid_count, left_on='자치구', right_on='SGG_NM', how='left')

# 7. 격자별 범죄 건수 분배
grid_sgg = grid_sgg.merge(crime_df, left_on='SGG_NM', right_on='자치구', how='left')
grid_sgg['전체_격자'] = grid_sgg['전체'] / grid_sgg['grid_count']

# 8. 결과 저장
save_cols = ['center_lon', 'center_lat', '전체_격자']
grid_sgg[save_cols].to_csv('crime_grid_10m.csv', index=False)
logger.info('격자별 범죄 데이터 저장 완료: crime_grid_10m.csv')

# 9. 시각화 (전체 격자 사용)
plot_data = grid_sgg[grid_sgg['전체_격자'] > 0]
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
heat_data = [[row['center_lat'], row['center_lon'], row['전체_격자']] for _, row in plot_data.iterrows()]
HeatMap(heat_data, radius=15, blur=10, min_opacity=0.2).add_to(m)
m.save('crime_grid_10m_map.html')
logger.info('지도 시각화 저장 완료: crime_grid_10m_map.html')

# shp 자치구명 리스트
print("shp 자치구명:", sorted(sgg_boundary['SGG_NM'].unique()))
# csv 자치구명 리스트
print("csv 자치구명:", sorted(df['자치구'].unique()))
# 매칭 안 되는 자치구
print("매칭 안 되는 자치구:", set(df['자치구'].unique()) - set(sgg_boundary['SGG_NM'].unique())) 