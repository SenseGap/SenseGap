import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from folium.plugins import HeatMap
import logging
from shapely.geometry import Point
import pyproj

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def smart_read_excel(path, *args, **kwargs):
    try:
        df = pd.read_excel(path, *args, **kwargs)
        logger.info(f"파일 {path}의 컬럼: {df.columns.tolist()}")
        return df
    except Exception as e:
        logger.error(f"엑셀 읽기 오류: {e}")
        raise

# 1. 토지이용현황도 분류체계 불러오기
landuse_code_path = '토지이용현황도_분류항목.xls'
landuse_codes = smart_read_excel(landuse_code_path, skiprows=4)
landuse_codes.columns = ['대분류', '중분류', '소분류', '코드', '정의', '비고']
landuse_codes = landuse_codes.dropna(subset=['코드'])

# 대분류 결측값 보정
landuse_codes['대분류'] = landuse_codes['대분류'].ffill()

# 코드 컬럼이 문자열인지 확인하고 변환
landuse_codes['코드'] = landuse_codes['코드'].astype(str)
logger.info(f"토지이용 분류체계 로드 완료. 행 수: {len(landuse_codes)}")
logger.info(f"대분류 목록: {landuse_codes['대분류'].unique().tolist()}")

# 2. 토지이용현황도 Shapefile 불러오기
landuse_shp_path = 'AL_D154_11_20250412.shp'
gdf = gpd.read_file(landuse_shp_path)
logger.info(f"토지이용현황도 데이터 로드 완료. 행 수: {len(gdf)}")

# 3. 좌표계 변환 (EPSG:5186 -> EPSG:4326)
gdf = gdf.to_crs(epsg=4326)
logger.info("좌표계 변환 완료 (EPSG:5186 -> EPSG:4326)")

# 4. 10m 격자 생성
grid_size_lat = 0.00009  # 위도 10m 근사값
grid_size_lon = 0.00011  # 경도 10m 근사값

# 격자 범위 계산
min_lon, min_lat, max_lon, max_lat = gdf.total_bounds
grid_x_min = int(min_lon // grid_size_lon)
grid_x_max = int(max_lon // grid_size_lon)
grid_y_min = int(min_lat // grid_size_lat)
grid_y_max = int(max_lat // grid_size_lat)

logger.info(f"격자 범위: X({grid_x_min}~{grid_x_max}), Y({grid_y_min}~{grid_y_max})")

# 격자 중심점 생성
grid_points = []
total_grids = (grid_x_max - grid_x_min + 1) * (grid_y_max - grid_y_min + 1)
logger.info(f"생성할 총 격자 수: {total_grids:,}개")

for x in range(grid_x_min, grid_x_max + 1):
    for y in range(grid_y_min, grid_y_max + 1):
        center_lon = (x + 0.5) * grid_size_lon
        center_lat = (y + 0.5) * grid_size_lat
        grid_points.append({
            'grid_x': x,
            'grid_y': y,
            'center_lon': center_lon,
            'center_lat': center_lat,
            'geometry': Point(center_lon, center_lat)
        })
        if len(grid_points) % 100000 == 0:
            logger.info(f"격자 생성 중... {len(grid_points):,}개 완료")

grid_gdf = gpd.GeoDataFrame(grid_points, crs='EPSG:4326')
logger.info(f"격자 생성 완료. 총 격자 수: {len(grid_gdf):,}개")

# 5. 공간 조인으로 격자별 토지이용 현황 집계
logger.info("공간 조인 시작... (시간이 다소 소요될 수 있습니다)")
joined = gpd.sjoin(grid_gdf, gdf, how='left', predicate='within')
logger.info(f"공간 조인 완료. 결과 행 수: {len(joined):,}개")

# 6. 토지이용 코드별 집계
logger.info("토지이용 코드별 집계 시작...")
landuse_counts = joined.groupby(['grid_x', 'grid_y', 'A12']).size().reset_index(name='count')
logger.info(f"집계 완료. 고유한 토지이용 코드 수: {landuse_counts['A12'].nunique()}개")

pivot = landuse_counts.pivot_table(
    index=['grid_x', 'grid_y'],
    columns='A12',
    values='count',
    fill_value=0
).reset_index()
logger.info(f"피벗 테이블 생성 완료. 행 수: {len(pivot):,}개")

# 8. 토지이용 코드와 분류명 매핑
code_to_name = dict(zip(landuse_codes['코드'], landuse_codes['대분류']))
rename_dict = {col: f"landuse_{code_to_name.get(str(col), col)}" for col in pivot.columns if col not in ['grid_x', 'grid_y']}
pivot = pivot.rename(columns=rename_dict)

# 7. 격자 중심 좌표 추가
pivot['center_lon'] = (pivot['grid_x'] + 0.5) * grid_size_lon
pivot['center_lat'] = (pivot['grid_y'] + 0.5) * grid_size_lat

# 9. 결과 저장
output_path = 'landuse_grid_10m.csv'
pivot.to_csv(output_path, index=False)
logger.info(f"격자별 토지이용 현황 저장 완료: {output_path}")

# 10. 지도 시각화 (주거지역 기준)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
residential_col = next((col for col in pivot.columns if '주거' in col), None)
if residential_col:
    heat_data = [[row['center_lat'], row['center_lon'], row[residential_col]] 
                 for _, row in pivot[pivot[residential_col] > 0].iterrows()]
    HeatMap(heat_data, radius=15, blur=10).add_to(m)
    map_path = 'landuse_grid_10m_map.html'
    m.save(map_path)
    logger.info(f"지도 시각화 저장 완료: {map_path}") 