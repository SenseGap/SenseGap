import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import logging
import pyproj
import geopandas as gpd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def smart_read_csv(path, *args, **kwargs):
    try:
        df = pd.read_csv(path, *args, **kwargs)
        logger.info(f"파일 {path}의 컬럼: {df.columns.tolist()}")
        return df
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding='cp949', *args, **kwargs)
        logger.info(f"파일 {path}의 컬럼: {df.columns.tolist()}")
        return df
    except Exception as e:
        logger.error(f"CSV 읽기 오류: {e}")
        raise

# 1. 서울시 경계 불러오기
seoul_boundary = gpd.read_file('LARD_ADM_SECT_SGG_11_202505.shp').to_crs(epsg=4326)

# 2. 경찰 데이터 불러오기 후 GeoDataFrame 변환
# (예시: df = pd.read_csv(...))
# gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['lon'], df['lat']), crs='EPSG:4326')

# 1. 치안시설 데이터 불러오기
police_path = '치안시설.csv'
df = smart_read_csv(police_path)

# 2. 위경도 컬럼명 자동 탐색 (원본 컬럼)
lat_col_orig = 'Y'  # 직접 지정
lon_col_orig = 'X'  # 직접 지정

logger.info(f"사용할 좌표 컬럼: {lon_col_orig}(경도), {lat_col_orig}(위도)")

# 원본 위경도/XY 데이터를 숫자형으로 변환 및 클렌징
df[lat_col_orig] = df[lat_col_orig].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
df[lon_col_orig] = df[lon_col_orig].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
df[lat_col_orig] = pd.to_numeric(df[lat_col_orig], errors='raise')
df[lon_col_orig] = pd.to_numeric(df[lon_col_orig], errors='raise')

# 변환 전 원본 컬럼의 NaN 개수 확인
logger.info(f"원본 {lat_col_orig} 컬럼 NaN 개수 (to_numeric 후): {df[lat_col_orig].isnull().sum()}")
logger.info(f"원본 {lon_col_orig} 컬럼 NaN 개수 (to_numeric 후): {df[lon_col_orig].isnull().sum()}")

# 결측치 제거
df = df.dropna(subset=[lat_col_orig, lon_col_orig])
logger.info(f"유효한 원본 좌표 데이터 수 (dropna 후): {len(df)}")

# 3. 좌표 변환 (EPSG:3857 -> EPSG:4326)
transformer = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

# 변환된 위경도 컬럼 생성
df['center_lon'], df['center_lat'] = transformer.transform(df[lon_col_orig].values, df[lat_col_orig].values)

logger.info(f"좌표 변환 완료. 변환된 데이터 수: {len(df)}")

# 변환된 위경도 컬럼의 NaN 개수 확인
logger.info(f"변환된 center_lat NaN 개수: {df['center_lat'].isnull().sum()}")
logger.info(f"변환된 center_lon NaN 개수: {df['center_lon'].isnull().sum()}")

# 변환된 좌표의 범위 확인
logger.info(f"변환된 위도 범위: {df['center_lat'].min()} ~ {df['center_lat'].max()}")
logger.info(f"변환된 경도 범위: {df['center_lon'].min()} ~ {df['center_lon'].max()}")

# 3. 서울시만 남기기
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['center_lon'], df['center_lat']), crs='EPSG:4326')
gdf = gpd.sjoin(gdf, seoul_boundary, how='inner', predicate='within')

grid_size = 0.00009

gdf['grid_x'] = (gdf['center_lon'] // grid_size).astype(int)
gdf['grid_y'] = (gdf['center_lat'] // grid_size).astype(int)

grid_counts = gdf.groupby(['grid_x', 'grid_y']).size().reset_index(name='police_count')

# 7. 격자 중심 좌표 계산 (변환된 위경도 사용)
grid_counts['center_lon'] = (grid_counts['grid_x'] + 0.5) * grid_size
grid_counts['center_lat'] = (grid_counts['grid_y'] + 0.5) * grid_size

# 8. 결과 저장
output_path = 'police_grid_10m.csv'
grid_counts.to_csv(output_path, index=False)
logger.info(f"격자별 치안시설 개수 저장 완료: {output_path}")

# 9. 데이터 확인
logger.info("\n=== 데이터 확인 ===")
logger.info(f"총 격자 수: {len(grid_counts)}")
logger.info(f"치안시설이 있는 격자 수: {len(grid_counts[grid_counts['police_count'] > 0])}")
logger.info("\n치안시설 개수 분포:")
logger.info(grid_counts['police_count'].describe())

# 10. 지도 시각화
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 히트맵 데이터 준비
heat_data = [[row['center_lat'], row['center_lon'], row['police_count']] 
             for _, row in grid_counts[grid_counts['police_count'] > 0].iterrows()]

# 히트맵 추가
HeatMap(heat_data, radius=15, blur=10).add_to(m)

# 지도 저장
map_path = 'police_grid_10m_map.html'
m.save(map_path)
logger.info(f"지도 시각화 저장 완료: {map_path}") 