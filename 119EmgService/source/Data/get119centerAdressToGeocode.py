#!/usr/bin/env python3
# coding: utf-8

import pandas as pd
import requests
import time

# ───────────────────────────────────────────────────────
# 설정
REST_KEY    = "28c046f4a78799253e8402cf498ff472"
HEADERS     = {"Authorization": f"KakaoAK {REST_KEY}"}
STATION_CSV = "소방청_시도 소방서 현황_20240630.csv"
CENTER_CSV  = "소방청_119안전센터 현황_20240630.csv"
OUTPUT_CSV  = "119serviceGeocoded.csv"

# ───────────────────────────────────────────────────────
# 1) CSV 로드
station_df = pd.read_csv(STATION_CSV, encoding="cp949")
center_df  = pd.read_csv(CENTER_CSV,  encoding="cp949")

# ───────────────────────────────────────────────────────
# 2) 컬럼명 통일 및 종류 표시
station_df = station_df.rename(
    columns={"소방서":"service_name", "주소":"address"}
)
station_df["service_type"] = "소방서"

center_df = center_df.rename(
    columns={"119안전센터명":"service_name", "주소":"address"}
)
center_df["service_type"] = "119안전센터"

# ───────────────────────────────────────────────────────
# 3) ‘서울특별시’ 주소만 필터링
station_df = station_df[station_df["address"].str.contains("서울특별시")]
center_df  = center_df [center_df ["address"].str.contains("서울특별시")]

# ───────────────────────────────────────────────────────
# 4) 구(district) 추출 (“서울특별시 강남구 …” → “강남구”)
for df in (station_df, center_df):
    df["district"] = df["address"].str.split().str[1]

# ───────────────────────────────────────────────────────
# 5) 합치기
df = pd.concat([station_df, center_df], ignore_index=True, sort=False)

# ───────────────────────────────────────────────────────
# 6) 카카오 지오코딩 함수
def geocode_kakao(address: str):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    params = {"query": address}
    res = requests.get(url, headers=HEADERS, params=params, timeout=5)
    if res.status_code != 200:
        return None, None
    docs = res.json().get("documents", [])
    if not docs:
        return None, None
    # 첫 번째 결과
    y = docs[0].get("y")
    x = docs[0].get("x")
    return float(y), float(x)

# ───────────────────────────────────────────────────────
# 7) 주소 → 위경도 일괄 처리
lats, lons = [], []
for addr in df["address"]:
    lat, lon = geocode_kakao(addr)
    lats.append(lat)
    lons.append(lon)
    time.sleep(0.2)  # 초당 최대 5회 권장

df["latitude"]  = lats
df["longitude"] = lons

# ───────────────────────────────────────────────────────
# 8) 최종 컬럼 정리 및 저장
cols   = ["service_type","service_name","address","district","latitude","longitude"]
others = [c for c in df.columns if c not in cols]
df     = df[cols + others]

df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
print(f"✅ '{OUTPUT_CSV}' 생성 완료!")
