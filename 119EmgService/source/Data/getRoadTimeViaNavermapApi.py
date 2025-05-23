import pandas as pd
import requests
import shelve
import sys

# ─── 설정 ─────────────────────────────────────────────────────────
CLIENT_ID     = "xrv14a9u9b"
CLIENT_SECRET = "wA2kxKswZWK4r9BmJfXjwGGtIga0iQyTYHZdV09z"
API_URL       = "https://maps.apigw.ntruss.com/map-direction/v1/driving"

# ─── 디스크 기반 캐시 열기 ─────────────────────────────────────────
# 캐시 파일 하나만 있으면, 재실행해도 이전 호출 결과를 재사용합니다.
cache = shelve.open("naver_directions_cache.db")

# ─── 세션 & 인증 헤더 ─────────────────────────────────────────────
session = requests.Session()
session.headers.update({
    "x-ncp-apigw-api-key-id": CLIENT_ID,
    "x-ncp-apigw-api-key":    CLIENT_SECRET,
})

# ─── 호출 카운터 ───────────────────────────────────────────────────
call_count = 0  # 실제 API 호출 횟수 (캐시 히트 제외)

def get_travel_time(o_lon, o_lat, d_lon, d_lat):
    """
    origin → destination 간 주행시간(초)을 반환.
    디스크 캐시에 있으면 재사용, 없으면 API 호출 후 캐시에 저장.
    """
    global call_count
    key = f"{o_lon},{o_lat}_{d_lon},{d_lat}"
    if key in cache:
        return cache[key]

    # 실제 API 호출
    call_count += 1
    if call_count % 100 == 0:
        print(f"→ {call_count}회 실제 API 호출…")

    params = {"start": f"{o_lon},{o_lat}", "goal": f"{d_lon},{d_lat}"}
    resp = session.get(API_URL, params=params, timeout=10)
    if resp.status_code == 401:
        print("❌ Unauthorized (401). 설정을 확인하세요.")
        sys.exit(1)
    resp.raise_for_status()

    data = resp.json().get("route", {})
    duration = None
    tra = data.get("traoptimal") or []
    if tra:
        duration = tra[0].get("summary", {}).get("duration")

    cache[key] = duration  # 디스크에 저장
    cache.sync()           # 즉시 디스크에 반영
    return duration

def get_weighted_travel_time(o_lon, o_lat, s_lons, s_lats, ratios):
    lon_parts   = str(s_lons).split(";")
    lat_parts   = str(s_lats).split(";")
    ratio_parts = str(ratios).split(";")
    total = 0.0

    for lon_str, lat_str, ratio_str in zip(lon_parts, lat_parts, ratio_parts):
        try:
            d_lon  = float(lon_str)
            d_lat  = float(lat_str)
            weight = float(ratio_str)
        except ValueError:
            continue
        t = get_travel_time(o_lon, o_lat, d_lon, d_lat) or 0
        total += t * weight

    return total

def main():
    df = pd.read_csv("gridNearest119CenterRoadFixed.csv", encoding="utf-8-sig")
    results = []

    for _, row in df.iterrows():
        o_lon = row["center_road_lon"]
        o_lat = row["center_road_lat"]
        if pd.isna(o_lon) or pd.isna(o_lat):
            results.append(None)
            continue

        wtime = get_weighted_travel_time(
            o_lon, o_lat,
            row["service_lon"],
            row["service_lat"],
            row.get("area_ratio", "1")
        )
        results.append(wtime)

    df["road_travel_time_s"] = results
    out_path = "gridRoadTime.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    # 캐시 닫기
    cache.close()

    print(f"\n✔ 완료! 실제 API 호출: {call_count}회")
    print(f"✔ 결과 파일: {out_path}")

if __name__ == "__main__":
    main()
