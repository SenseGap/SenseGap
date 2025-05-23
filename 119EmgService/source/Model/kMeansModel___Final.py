# clustering_and_visualization_updated.py

# --- Part 1: 클러스터링 및 등급 매핑 (Dataset2_updated.csv 사용) ---
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# 1) 데이터 불러오기
df = pd.read_csv('Dataset2_updated.csv', encoding='utf-8-sig')

# 2) 수치형 특성 선택 (식별자·위치 제외)
exclude = ['orig_idx', 'center_lon', 'center_lat']
features = [
    c for c, t in df.dtypes.items()
    if t in ('int64', 'float64') and c not in exclude
]
print("사용할 특성:", features)

# 3) 결측값 평균 대체 & 4) 표준화
X = SimpleImputer(strategy='mean').fit_transform(df[features])
X_scaled = StandardScaler().fit_transform(X)

# 5) KMeans(10 clusters)
km = KMeans(n_clusters=10, random_state=0)
labels = km.fit_predict(X_scaled)
df['cluster'] = labels

# 6) infra_score 계산 (표준화된 특성 합)
df['infra_score'] = X_scaled.sum(axis=1)

# 7) cluster → grade 매핑
means = df.groupby('cluster')['infra_score'].mean().sort_values()
grade_map = {cluster: rank + 1 for rank, cluster in enumerate(means.index)}
df['infra_grade'] = df['cluster'].map(grade_map)

# 8) 결과 저장
out_grade = 'Dataset2_updated_infra_grade.csv'
df.to_csv(out_grade, index=False, encoding='utf-8-sig')
print(f"✅ 저장 완료: {out_grade}")

# --- Part 2: Folium 시각화 (새로 생성된 등급파일 사용) ---
import math
import folium
import os
from branca.colormap import linear

# 파일 경로
grid_fp = 'Dataset2_updated_infra_grade.csv'
geo_fp  = 'address_geocode.csv'

# 파일 확인
if not os.path.exists(grid_fp) or not os.path.exists(geo_fp):
    raise FileNotFoundError("두 파일 모두 스크립트와 동일 폴더에 위치시켜 주세요.")

# 데이터 로드
df_grid = pd.read_csv(grid_fp, encoding='utf-8-sig')
df_geo  = pd.read_csv(geo_fp,  encoding='utf-8-sig')

# NaN 제거
df_grid = df_grid.dropna(subset=['center_lat', 'center_lon', 'infra_grade']).reset_index(drop=True)
df_geo  = df_geo.dropna(subset=['lat', 'lon']).reset_index(drop=True)

# 격자 반변(m) → 위/경도 차이 계산 함수
def meter_to_deg_lat(m): return m / 111000
def meter_to_deg_lon(m, lat): return m / (111000 * math.cos(math.radians(lat)))

half_side = 125
df_grid['dlat'] = df_grid['center_lat'].apply(lambda lat: meter_to_deg_lat(half_side))
df_grid['dlon'] = df_grid.apply(lambda r: meter_to_deg_lon(half_side, r['center_lat']), axis=1)

# 지도 초기화
mean_lat = df_grid['center_lat'].mean()
mean_lon = df_grid['center_lon'].mean()
m = folium.Map(location=[mean_lat, mean_lon], zoom_start=11)

# 컬러맵 생성 (1~10등급)
colormap = linear.YlOrRd_09.scale(1, 10)
colormap.caption = 'Infra Grade (1 low → 10 high)'
m.add_child(colormap)

# 격자 폴리곤 추가 (등급별 색상)
for _, r in df_grid.iterrows():
    sw = [r['center_lat'] - r['dlat'], r['center_lon'] - r['dlon']]
    ne = [r['center_lat'] + r['dlat'], r['center_lon'] + r['dlon']]
    grade = int(r['infra_grade'])
    color = colormap(grade)
    folium.Rectangle(
        bounds=[sw, ne],
        color=color,
        weight=1,
        fill=True,
        fill_color=color,
        fill_opacity=0.5,
        popup=f"Grid {r['orig_idx']}<br>Grade {grade}"
    ).add_to(m)

# 소방서·안전센터 표시
stations = df_geo[df_geo['type'] == 'station']
centers  = df_geo[df_geo['type'] == 'center']
station_coords = set(zip(stations['lat'], stations['lon']))

# 소방서: 파란색 사각형
for _, r in stations.iterrows():
    folium.RegularPolygonMarker(
        location=[r['lat'], r['lon']],
        number_of_sides=4,
        radius=8,
        color='blue', fill=True, fill_color='blue', fill_opacity=0.7,
        popup=r['address']
    ).add_to(m)

# 안전센터: 녹색 삼각형 (소방서 겹침 제외)
for _, r in centers.iterrows():
    if (r['lat'], r['lon']) in station_coords:
        continue
    folium.RegularPolygonMarker(
        location=[r['lat'], r['lon']],
        number_of_sides=3,
        radius=8,
        color='green', fill=True, fill_color='green', fill_opacity=0.7,
        popup=r['address']
    ).add_to(m)

# HTML 저장
m.save('fire_infra_map.html')
print("✅ 인터랙티브 지도 저장: fire_infra_map.html")
