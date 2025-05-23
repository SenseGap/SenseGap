import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

# 1) 파일 경로
GRID_CSV   = '1.1.csv'
RISK_SHP   = 'C0700038F00002.shp'
OUTPUT_CSV = '1.1_with_fire_risk.csv'

# 2) 1.1.csv 읽기
grid_df = pd.read_csv(GRID_CSV, encoding='utf-8')

# 3) Point → 격자 폴리곤(250m×250m) 생성
#   - WGS84(lon/lat) 포인트를 TM(5179)으로 변환 후, cap_style=3 로 buffer 하면 정사각형
pts = gpd.GeoDataFrame(
    grid_df,
    geometry=gpd.points_from_xy(grid_df.center_lon, grid_df.center_lat),
    crs='epsg:4326'  # WGS84
)
pts = pts.to_crs(epsg=5179)  # 서울 TM

# 반변 길이 125m 인 사각형(buffer cap_style=3)
pts['geometry'] = pts.geometry.buffer(125, cap_style=3)

# 원래 index를 보존하기 위해 컬럼으로 옮기기
pts = pts.reset_index().rename(columns={'index':'orig_idx'})

# 4) 화재위험 shapefile 읽기 및 CRS 일치
risk = gpd.read_file(RISK_SHP).to_crs(pts.crs)

# 5) GRAD(A~D) → 숫자 매핑 (원하는 값으로 조정 가능)
grade_to_numeric = {'A':1, 'B':4, 'C':7, 'D':10}
risk['risk_num'] = risk['GRAD'].map(grade_to_numeric)

# 6) 교차 영역 계산
#    결과에 orig_idx, risk_num, geometry(교차 폴리곤) 포함
inter = gpd.overlay(
    pts[['orig_idx','geometry']],
    risk[['geometry','risk_num']],
    how='intersection'
)

# 7) 면적 비율(weight) 계산
inter['area']   = inter.geometry.area
cell_area       = pts.geometry.iloc[0].area
inter['weight'] = inter['area'] / cell_area

# 8) 가중평균 risk_score 계산
inter['weighted'] = inter['risk_num'] * inter['weight']
agg = (inter
       .groupby('orig_idx')['weighted']
       .sum()
       .rename('risk_score'))

# 9) 원본 pts 에 붙이고, NaN은 0으로 처리
pts = pts.set_index('orig_idx').join(agg).reset_index()
pts['risk_score'] = pts['risk_score'].fillna(0)

# 10) 결과를 CSV 로 저장 (geometry는 제외하거나 WKT로 바꿀 수 있음)
out = pts.drop(columns='geometry')
out.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

print(f"✔ '{OUTPUT_CSV}' 생성 완료")
