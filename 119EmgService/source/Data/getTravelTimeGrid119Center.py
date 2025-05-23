import pandas as pd
import requests
import time
import shelve

API_KEY  = "28c046f4a78799253e8402cf498ff472"
BASE_URL = "https://apis-navi.kakaomobility.com/v1/directions"
HEADERS  = {"Authorization": f"KakaoAK {API_KEY}"}

# 디스크 기반 캐시
cache = shelve.open("travel_time_cache.db")

def get_travel_time(lon1, lat1, lon2, lat2, max_retries=3):
    key = f"{lon1},{lat1}_{lon2},{lat2}"
    if key in cache:
        return cache[key]

    params = {
        "origin":      f"{lon1},{lat1}",
        "destination": f"{lon2},{lat2}",
        # summary, alternatives 등은 기본값 사용
    }

    for attempt in range(1, max_retries+1):
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10)
        if not resp.ok:
            print(f"[{resp.status_code}] 요청 실패: {resp.text.strip()}")
            time.sleep(2 ** attempt)
            continue

        data = resp.json()
        # routes → summary → duration 접근 전 방어 로직
        routes = data.get("routes")
        if not routes:
            print("▶ 'routes'가 없습니다:", data)
            return None

        summary = routes[0].get("summary") if isinstance(routes[0], dict) else None
        if not summary or "duration" not in summary:
            print("▶ 'summary.duration'를 찾을 수 없습니다:", data)
            return None

        duration = summary["duration"]
        cache[key] = duration
        return duration

    # 최대 재시도 후에도 실패
    print(f"⚠️ {key} 호출 실패 (재시도 {max_retries}회), None 반환")
    return None

def compute_avg_times(in_csv, out_csv=None):
    df = pd.read_csv(in_csv)
    results = []

    for _, row in df.iterrows():
        cx, cy = row["center_lon"], row["center_lat"]
        slons  = str(row["service_lon"]).split(";")
        slats  = str(row["service_lat"]).split(";")
        ratios = str(row.get("area_ratio", "1")).split(";")

        total = 0.0
        for lon, lat, r in zip(slons, slats, ratios):
            dur = get_travel_time(cx, cy, float(lon), float(lat))
            total += (dur or 0) * float(r)
            time.sleep(0.2)  # 호출 빈도에 맞춰 조절
        results.append(total)

    df["avg_travel_time"] = results
    if out_csv:
        df.to_csv(out_csv, index=False)
    cache.close()
    return df

if __name__ == "__main__":
    result = compute_avg_times(
        "gridNearest119Center.csv",
        "gridNearest119Center_with_time.csv"
    )
    print(result.head())
