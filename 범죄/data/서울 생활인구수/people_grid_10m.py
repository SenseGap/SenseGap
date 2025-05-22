import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import logging
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

# 1. 행정동 경계 불러오기
dong_boundary = gpd.read_file('LARD_ADM_SECT_SGG_11_202505.shp').to_crs(epsg=4326)
logger.info(f"행정동 경계 데이터 컬럼: {dong_boundary.columns.tolist()}")

# 2. 인구 데이터 불러오기 (청크 단위로 처리)
people_path = 'LOCAL_PEOPLE_DONG_202504.csv'
chunk_size = 100000  # 청크 크기 조정

# 필요한 컬럼만 선택
needed_columns = ['행정동코드', '총생활인구수']

# 청크 단위로 데이터 처리
chunks = []
for chunk in pd.read_csv(people_path, chunksize=chunk_size, usecols=needed_columns):
    # 행정동 코드 형식 통일
    chunk['행정동코드'] = chunk['행정동코드'].astype(str).str.split('.').str[0]
    # 시간대 구분 없이 행정동별 인구 합산
    chunk = chunk.groupby(['행정동코드'])['총생활인구수'].sum().reset_index()
    # 메모리 효율적인 데이터 타입 사용
    chunk['행정동코드'] = chunk['행정동코드'].astype('category')
    chunk['총생활인구수'] = chunk['총생활인구수'].astype('float32')
    chunks.append(chunk)
# 청크 병합
df = pd.concat(chunks, ignore_index=True)
df = df.groupby(['행정동코드'])['총생활인구수'].sum().reset_index()

# 3. 행정동 코드 매칭을 위한 컬럼 확인
logger.info("\n=== 데이터 확인 ===")
logger.info(f"인구 데이터 컬럼: {df.columns.tolist()}")
logger.info(f"행정동 경계 데이터 컬럼: {dong_boundary.columns.tolist()}")

# 행정동 코드 형식 확인
logger.info("\n=== 행정동 코드 형식 확인 ===")
logger.info(f"인구 데이터 행정동코드 예시: {df['행정동코드'].iloc[0]}")
logger.info(f"행정동 경계 데이터 코드 예시: {dong_boundary.iloc[0].to_dict()}")

dong_boundary['ADM_SECT_C'] = dong_boundary['ADM_SECT_C'].astype(str)

# 4. 10m 격자 생성
grid_size = 0.00009  # 약 10m

# 격자 범위 설정 (서울시 전체)
min_lon = dong_boundary.total_bounds[0]
max_lon = dong_boundary.total_bounds[2]
min_lat = dong_boundary.total_bounds[1]
max_lat = dong_boundary.total_bounds[3]

# 격자 인덱스 생성
x_indices = np.arange(min_lon, max_lon, grid_size)
y_indices = np.arange(min_lat, max_lat, grid_size)

# 격자 중심점 생성
grid_points = []
for x in x_indices:
    for y in y_indices:
        grid_points.append({
            'center_lon': x + grid_size/2,
            'center_lat': y + grid_size/2
        })

# 격자 중심점을 GeoDataFrame으로 변환
grid_gdf = gpd.GeoDataFrame(
    grid_points,
    geometry=gpd.points_from_xy([p['center_lon'] for p in grid_points], 
                              [p['center_lat'] for p in grid_points]),
    crs='EPSG:4326'
)

# 5. 격자와 행정동 매칭
grid_dong = gpd.sjoin(grid_gdf, dong_boundary, how='inner', predicate='within')

# 6. 행정동별 격자 개수 계산
dong_grid_count = grid_dong.groupby('ADM_SECT_C').size().reset_index(name='grid_count')

# 7. 인구 데이터와 격자 개수 merge
df = df.merge(dong_grid_count, left_on='행정동코드', right_on='ADM_SECT_C', how='left')

# 8. 격자별 인구수 = (행정동별 인구수) / (해당 행정동의 격자 개수)
grid_dong = grid_dong.merge(df, left_on='ADM_SECT_C', right_on='행정동코드', how='left')
grid_dong['격자_인구수'] = grid_dong['총생활인구수'] / grid_dong['grid_count']

# 9. 격자별 인구 집계
grid_counts = grid_dong.groupby(['center_lon', 'center_lat'])['격자_인구수'].sum().reset_index()

# 10. 결과 저장
output_path = 'people_grid_10m.csv'
grid_counts.to_csv(output_path, index=False)
logger.info(f"격자별 인구 데이터 저장 완료: {output_path}")

# 11. 데이터 확인
logger.info("\n=== 데이터 확인 ===")
logger.info(f"총 격자 수: {len(grid_counts)}")
logger.info(f"인구가 있는 격자 수: {len(grid_counts[grid_counts['격자_인구수'] > 0])}")
logger.info("\n인구 분포:")
logger.info(grid_counts['격자_인구수'].describe())

# 12. 지도 시각화 (전체 인구 기준 1개 파일만 생성)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
heat_data = [[row['center_lat'], row['center_lon'], row['격자_인구수']] 
             for _, row in grid_counts[grid_counts['격자_인구수'] > 0].iterrows()]
HeatMap(heat_data, radius=15, blur=10).add_to(m)
map_path = 'people_grid_10m_map.html'
m.save(map_path)
logger.info(f"지도 시각화 저장 완료: {map_path}") 