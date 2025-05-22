import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def smart_read_excel(path, *args, **kwargs):
    try:
        df = pd.read_excel(path, *args, **kwargs)
        logger.info(f"파일 {path}의 컬럼: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        logger.error(f"오류: 파일을 찾을 수 없습니다 - {path}")
        raise
    except Exception as e:
        logger.error(f"Excel 파일 읽기 오류: {e}")
        raise

# 1. CCTV (Excel) 데이터 불러오기
excel_path = 'seoul_cctv_locations.xlsx'
df = smart_read_excel(excel_path)

# 2. 위경도 컬럼 직접 지정
lat_col_orig = 'LA' # 위도 컬럼
lon_col_orig = 'LO' # 경도 컬럼

logger.info(f"사용할 좌표 컬럼: {lon_col_orig}(경도), {lat_col_orig}(위도)")

# 원본 위경도 데이터를 숫자형으로 변환 및 클렌징
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

# 데이터는 이미 위경도(EPSG:4326)로 추정되므로 좌표 변환 생략
df['center_lat'] = df[lat_col_orig]
df['center_lon'] = df[lon_col_orig]

logger.info(f"좌표 처리 완료. 처리된 데이터 수: {len(df)}")
logger.info(f"변환된 center_lat NaN 개수: {df['center_lat'].isnull().sum()}")
logger.info(f"변환된 center_lon NaN 개수: {df['center_lon'].isnull().sum()}")
logger.info(f"변환된 위도 범위: {df['center_lat'].min()} ~ {df['center_lat'].max()}")
logger.info(f"변환된 경도 범위: {df['center_lon'].min()} ~ {df['center_lon'].max()}")

# 3. 격자 크기 설정 (10m)
# EPSG:4326에서 10m는 위도에 따라 달라지므로 근사값 사용 (서울 기준)
grid_size_lat = 0.00009  # 서울 위도 기준 약 10m에 해당하는 위도 변화량 (근사)
grid_size_lon = 0.00011 # 서울 위도 기준 약 10m에 해당하는 경도 변화량 (근사)

# 4. 격자 인덱스 생성
df['grid_x'] = (df['center_lon'] // grid_size_lon).astype(int)
df['grid_y'] = (df['center_lat'] // grid_size_lat).astype(int)

# 5. 격자별 CCTV 개수 집계
grid_counts = df.groupby(['grid_x', 'grid_y']).size().reset_index(name='cctv_location_count')

# 6. 격자 중심 좌표 계산
grid_counts['center_lon'] = (grid_counts['grid_x'] + 0.5) * grid_size_lon
grid_counts['center_lat'] = (grid_counts['grid_y'] + 0.5) * grid_size_lat

# 7. 결과 저장
output_path = 'seoul_cctv_locations_grid_10m.csv'
grid_counts.to_csv(output_path, index=False)
logger.info(f"격자별 CCTV 개수 저장 완료: {output_path}")

# 8. 데이터 확인
logger.info("\n=== 데이터 확인 ===")
logger.info(f"총 격자 수: {len(grid_counts)}")
logger.info(f"CCTV가 있는 격자 수: {len(grid_counts[grid_counts['cctv_location_count'] > 0])}")
logger.info("\nCCTV 개수 분포:")
logger.info(grid_counts['cctv_location_count'].describe())

# 9. 지도 시각화
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

# 히트맵 데이터 준비
heat_data = [[row['center_lat'], row['center_lon'], row['cctv_location_count']] 
             for _, row in grid_counts[grid_counts['cctv_location_count'] > 0].iterrows()]

# 히트맵 추가
HeatMap(heat_data, radius=15, blur=10).add_to(m)

# 지도 저장
map_path = 'seoul_cctv_locations_grid_10m_map.html'
m.save(map_path)
logger.info(f"지도 시각화 저장 완료: {map_path}") 