# 🏪 서울시 상가 정보 데이터 (10m 격자 기반)

## 📌 개요
- 서울시 소상공인시장진흥공단에서 제공하는 상가(상권) 정보를 기반으로, 약 10m 단위 격자로 분할하여 격자별 상가 수 및 업종별 분포를 집계한 공간 데이터입니다.
- 분석 목적: 상권 밀집 지역 파악, 업종 분포 분석, 상권 공백지대 탐지 및 상업 전략 수립 지원

## 🛠 전처리 개요
- 원본 형식: CSV (`소상공인시장진흥공단_상가상권정보_서울_202503.csv`)
- 주요 열:
  - `위도`, `경도`: 상가 위치
  - `상가업소번호`: 개체 식별용
  - `상권업종대분류명`: 업종 대분류명 (예: 음식, 서비스, 소매 등)
- 전처리 절차:
  - 위경도 컬럼 정제 및 숫자형 변환
  - 위경도 기반 격자 인덱스(`grid_x`, `grid_y`) 생성
  - 격자별 업종 대분류 기준 `pivot_table`로 집계
  - 전체 합계를 `store_count`로 계산 후 좌표 추가

## 🔁 전처리 코드 개요
- 사용 파일: `store_grid_10m.py`
- 사용 언어: Python
- 주요 라이브러리: `pandas`, `numpy`, `folium`
- 처리 순서:
  1. CSV 파일 로딩 및 위경도 정제
  2. 격자 크기(위도 0.00009, 경도 0.00011) 기준 격자 인덱스 생성
  3. 업종 대분류명 기준 `pivot_table`로 업종별 상가 수 집계
  4. 격자 중심 좌표 추가 및 전체 합계 컬럼(`store_count`) 생성
  5. `store_grid_10m.csv` 저장 및 히트맵 시각화

## 📂 전처리 결과
- 저장 파일: `store_grid_10m.csv`
- 컬럼:
  - `grid_x`, `grid_y`: 격자 인덱스
  - `center_lon`, `center_lat`: 격자 중심 좌표
  - `store_count`: 격자 내 상가 총합
  - `업종별 상가 수`: 예) `음식`, `서비스`, `소매` 등
- 시각화 파일: `store_grid_10m_map.html` (Folium 기반 히트맵)

## 🏛 출처
- 데이터 출처: [공공데이터포털 - 소상공인시장진흥공단_상가(상권)정보](https://www.data.go.kr/data/15083033/fileData.do)
- 데이터 기준일: 2024년 3월 31일  
- Shapefile 출처: [국토정보플랫폼 - 시도/시군구 경계](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?datIde=30604&dsId=30604&pageIndex=1&pageSize=10&pageUnit=10&paginationInfo=egovframework.rte.ptl.mvc.tags.ui.pagination.PaginationInfo%40a0667c6&datPageIndex=2&datPageSize=10)

## 📌 참고 사항
- 격자 크기 기준: 위도 0.00009도, 경도 0.00011도 (서울 기준 약 10m)
- 일부 격자는 특정 업종만 포함하거나 상가가 존재하지 않을 수 있음
- 분석 목적에 따라 특정 업종만 필터링하거나 상가 총량 기준으로 가중치 부여 가능

