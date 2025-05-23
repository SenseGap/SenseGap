import pandas as pd

# 1) 원본 CSV 로드 (UTF-8 BOM 포함 가능성 대응)
df = pd.read_csv("gridRoadTime.csv", encoding="utf-8-sig")

# 2) 밀리초(ms) → 초(s) 변환, 소수점 제거(정수형)
df["road_travel_time_s"] = (df["road_travel_time_s"] / 1000).astype(int)

# 3) 수정된 결과 저장
output_path = "gridRoadTimeFixed.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")

# 4) 결과 미리보기
print(df[["center_road_lon", "center_road_lat", "road_travel_time_s"]].head())
print(f"\n✔ Saved fixed file: {output_path}")
