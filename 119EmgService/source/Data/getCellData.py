import pandas as pd
import numpy as np
from pyproj import Transformer

# --- 상수 정의 ---
CITY_HALL_LON, CITY_HALL_LAT = 126.9778222, 37.5664056  # 서울시청 기준 WGS84 좌표
GRID_RANGE = 20000    # 격자 생성 반경 (m)
INTERVAL   = 250      # 격자 크기/간격 (m)

# --- 좌표 변환 트랜스포머 ---
to_tm  = Transformer.from_crs("epsg:4326", "epsg:5181", always_xy=True)
to_wgs = Transformer.from_crs("epsg:5181", "epsg:4326", always_xy=True)

# 1) 서울시청 좌표를 TM(동부원점)로 변환
cityhall_x, cityhall_y = to_tm.transform(CITY_HALL_LON, CITY_HALL_LAT)

# 2) X/Y 범위 생성
x_vals = np.arange(cityhall_x - GRID_RANGE,
                   cityhall_x + GRID_RANGE + INTERVAL,
                   INTERVAL)
y_vals = np.arange(cityhall_y - GRID_RANGE,
                   cityhall_y + GRID_RANGE + INTERVAL,
                   INTERVAL)

# 3) 격자 중심 좌표 리스트 작성
grid_list = []
grid_id = 1
for y in y_vals:
    for x in x_vals:
        lon, lat = to_wgs.transform(x, y)
        grid_list.append({
            "GRID_ID":      grid_id,
            "X_CENTER_TM":  x,
            "Y_CENTER_TM":  y,
            "LONGITUDE":    lon,
            "LATITUDE":     lat
        })
        grid_id += 1

# 4) DataFrame 생성 및 CSV 저장
df_grid = pd.DataFrame(grid_list)
output_csv = "격자_센터_좌표.csv"
df_grid.to_csv(output_csv, index=False, encoding="utf-8-sig")

# 결과 확인 (샘플)
df_grid.head(), f"저장된 파일: {output_csv}"
