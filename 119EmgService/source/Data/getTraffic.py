import requests
import pandas as pd

# ── 사용자 설정 ──
TDATA_API_KEY = "YOUR_TDATA_API_KEY"  # 교통빅데이터포털에서 발급받은 인증키

# ── 1. 공간 링크 정보 조회 (linkId → linkDstnc) ──
def fetch_link_info():
    url = "http://t-data.seoul.go.kr/apig/apiman-gateway/tapi/BisTbisMsSpaceLink/1.0"
    link_info = {}
    start_row, row_cnt = 1, 1000

    while True:
        params = {
            "apikey": TDATA_API_KEY,
            "startRow": start_row,
            "rowCnt": row_cnt
        }
        res = requests.get(url, params=params)
        data = res.json()
        items = data.get("list", [])
        if not items:
            break

        for item in items:
            link_id = str(item["linkId"])
            distance_m = float(item["linkDstnc"])
            link_info[link_id] = distance_m

        start_row += row_cnt

    return link_info

# ── 2. 구간별 속도 정보 조회 (date 기준) ──
def fetch_section_stats(date):
    url = "http://t-data.seoul.go.kr/apig/apiman-gateway/tapi/TopisIccStTimesLinkTrfSectionStats/1.0"
    stats = []
    start_row, row_cnt = 1, 1000

    while True:
        params = {
            "apikey": TDATA_API_KEY,
            "stndDt": date,       # 기준일 (YYYYMMDD)
            "startRow": start_row,
            "rowCnt": row_cnt
        }
        res = requests.get(url, params=params)
        data = res.json()
        items = data.get("list", [])
        if not items:
            break

        stats.extend(items)
        start_row += row_cnt

    return stats

# ── 3. 메인 처리 ──
def main():
    # 예시: 2023년 5월 1일 데이터 조회
    date = "20230501"

    # 1) 링크 길이 정보 가져오기
    link_info = fetch_link_info()

    # 2) 평균 속도 정보 가져오기
    stats = fetch_section_stats(date)

    # 3) DataFrame 구성 및 계산
    df = pd.DataFrame(stats)
    df["linkId"] = df["linkId"].astype(str)
    df["avgSpd"] = df["avgSpd"].astype(float)

    # linkDstnc(m) → km
    df["distance_km"] = df["linkId"].map(link_info).fillna(0) / 1000

    # travel time (sec)
    df["travel_time_sec"] = (df["distance_km"] / df["avgSpd"]) * 3600

    # CSV로 저장
    df.to_csv("road_travel_time.csv", index=False)
    print("✅ road_travel_time.csv 파일이 생성되었습니다.")

if __name__ == "__main__":
    main()
