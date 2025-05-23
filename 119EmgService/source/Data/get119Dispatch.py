import pandas as pd
import numpy as np
import geopandas as gpd
from scipy.spatial import cKDTree

# ——— 1) 원본 격자 데이터 불러오기 ———
df_orig = pd.read_csv('gridData.csv', encoding='utf-8')
df_orig = df_orig[['i','j','center_lon','center_lat']].copy()
df_orig['grid_id'] = df_orig.index

# ——— 2) TM 투영 및 KD-Tree용 DataFrame 분리 ———
#   (원본 df_orig 은 건드리지 않고 별도 복사본으로만 투영)
df_tree = df_orig.copy()
gdf = gpd.GeoDataFrame(
    df_tree,
    geometry=gpd.points_from_xy(df_tree.center_lon, df_tree.center_lat),
    crs='epsg:4326'
).to_crs(epsg=5181)

df_tree['x_center'] = gdf.geometry.x
df_tree['y_center'] = gdf.geometry.y

coords = np.vstack([df_tree.x_center, df_tree.y_center]).T
tree   = cKDTree(coords)
half   = 125  # 격자 반변(m)

# ——— 3) 연도별 출동 건수 누적 ———
years = [2019, 2020, 2021, 2022, 2023]
total_counts = pd.Series(0, index=df_tree['grid_id'], dtype=int)

for year in years:
    infile = f'119신고접수 건별 격자 정보_{year}_서울.csv'
    df_inc = pd.read_csv(infile, encoding='cp949')
    
    # 필터링 & “출동” 스케일만
    df_inc = df_inc.dropna(subset=['LOC_INFO_X','LOC_INFO_Y'])
    df_inc = df_inc[~((df_inc.LOC_INFO_X == 0)&(df_inc.LOC_INFO_Y == 0))]
    df_inc = df_inc[df_inc['EGNCR_SCALE_NM'].str.contains('출동', na=False)]
    
    # 투영
    gdf_inc = gpd.GeoDataFrame(
        df_inc,
        geometry=gpd.points_from_xy(df_inc.LOC_INFO_X, df_inc.LOC_INFO_Y),
        crs='epsg:4326'
    ).to_crs(epsg=5181)
    
    inc_x = gdf_inc.geometry.x.values
    inc_y = gdf_inc.geometry.y.values
    mask_f = np.isfinite(inc_x)&np.isfinite(inc_y)
    inc_x, inc_y = inc_x[mask_f], inc_y[mask_f]
    
    # KD-Tree 할당
    dists, idxs = tree.query(np.vstack([inc_x, inc_y]).T, k=1)
    dx = np.abs(inc_x - df_tree.loc[idxs, 'x_center'].values)
    dy = np.abs(inc_y - df_tree.loc[idxs, 'y_center'].values)
    mask = (dx <= half)&(dy <= half)
    assigned = np.where(mask, df_tree.loc[idxs, 'grid_id'].values, -1)
    
    # 연도별 합산
    cnt = pd.Series(assigned[assigned>=0]).value_counts()
    total_counts = total_counts.add(cnt, fill_value=0).astype(int)

# ——— 4) 원본 좌표에 누적 결과 매핑 & 저장 ———
df_out = df_orig.copy()
df_out['dispatch_count_total'] = df_out['grid_id'].map(total_counts).fillna(0).astype(int)

df_out.to_csv('grid119Dispatch_total.csv', index=False, encoding='utf-8-sig')
print("완료: grid119Dispatch_total.csv 생성됨")
