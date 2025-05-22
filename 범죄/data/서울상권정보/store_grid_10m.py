import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def smart_read_csv(path, *args, **kwargs):
    try:
        df = pd.read_csv(path, *args, **kwargs)
        logger.info(f"파일 {path}의 컬럼: {df.columns.tolist()}")
        return df
    except Exception as e:
        logger.error(f"CSV 읽기 오류: {e}")
        raise

# 1. 상가정보 데이터 불러오기
store_path = '소상공인시장진흥공단_상가상권정보_서울_202503.csv'
df = smart_read_csv(store_path, encoding='utf-8')

# 2. 위경도 컬럼 직접 지정
lat_col_orig = '위도'
lon_col_orig = '경도'
logger.info(f"사용할 좌표 컬럼: {lon_col_orig}(경도), {lat_col_orig}(위도)")

df[lat_col_orig] = df[lat_col_orig].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
df[lon_col_orig] = df[lon_col_orig].astype(str).str.replace(r'[^0-9.-]', '', regex=True)
df[lat_col_orig] = pd.to_numeric(df[lat_col_orig], errors='raise')
df[lon_col_orig] = pd.to_numeric(df[lon_col_orig], errors='raise')

logger.info(f"원본 {lat_col_orig} 컬럼 NaN 개수 (to_numeric 후): {df[lat_col_orig].isnull().sum()}")
logger.info(f"원본 {lon_col_orig} 컬럼 NaN 개수 (to_numeric 후): {df[lon_col_orig].isnull().sum()}")

df = df.dropna(subset=[lat_col_orig, lon_col_orig])
logger.info(f"유효한 원본 좌표 데이터 수 (dropna 후): {len(df)}")

df['center_lat'] = df[lat_col_orig]
df['center_lon'] = df[lon_col_orig]

logger.info(f"좌표 처리 완료. 처리된 데이터 수: {len(df)}")
logger.info(f"변환된 center_lat NaN 개수: {df['center_lat'].isnull().sum()}")
logger.info(f"변환된 center_lon NaN 개수: {df['center_lon'].isnull().sum()}")
logger.info(f"변환된 위도 범위: {df['center_lat'].min()} ~ {df['center_lat'].max()}")
logger.info(f"변환된 경도 범위: {df['center_lon'].min()} ~ {df['center_lon'].max()}")

# 3. 격자 크기 설정 (10m)
grid_size_lat = 0.00009  # 위도 10m 근사값
grid_size_lon = 0.00011 # 경도 10m 근사값

# 4. 격자 인덱스 생성
df['grid_x'] = (df['center_lon'] // grid_size_lon).astype(int)
df['grid_y'] = (df['center_lat'] // grid_size_lat).astype(int)

# 5. 격자별 업종별 개수 피벗 (대분류)
pivot = df.pivot_table(
    index=['grid_x', 'grid_y'],
    columns='상권업종대분류명',
    values='상가업소번호',
    aggfunc='count',
    fill_value=0
).reset_index()

# 업종별 컬럼명 추출
category_names = [col for col in pivot.columns if col not in ['grid_x', 'grid_y']]
category_names = [col if isinstance(col, str) else col[-1] for col in category_names]

# 업종별 합계로 store_count 생성
pivot['store_count'] = pivot[category_names].sum(axis=1)

# center_lon, center_lat 추가
pivot['center_lon'] = (pivot['grid_x'] + 0.5) * grid_size_lon
pivot['center_lat'] = (pivot['grid_y'] + 0.5) * grid_size_lat

# 컬럼 순서: grid_x, grid_y, center_lon, center_lat, store_count, 업종별...
cols = ['grid_x', 'grid_y', 'center_lon', 'center_lat', 'store_count'] + category_names
pivot = pivot[cols]

# 결과 저장
output_path = 'store_grid_10m.csv'
pivot.to_csv(output_path, index=False)
logger.info(f"격자별 상가(전체+업종별) 개수 저장 완료: {output_path}")

# 지도 시각화 (store_count 기준)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)
heat_data = [[row['center_lat'], row['center_lon'], row['store_count']] 
             for _, row in pivot[pivot['store_count'] > 0].iterrows()]
HeatMap(heat_data, radius=15, blur=10).add_to(m)
map_path = 'store_grid_10m_map.html'
m.save(map_path)
logger.info(f"지도 시각화 저장 완료: {map_path}") 