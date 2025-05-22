# 📣 안전비상벨 위치 데이터 (10m 격자 기반)

## 📌 개요
- 서울시 내 보행자 긴급 호출용 안전비상벨 설치 위치 데이터를 바탕으로, 서울 전체를 약 10m 단위 격자로 나누어 격자별 비상벨 개수를 집계한 공간 데이터입니다.
- 분석 목적: 취약지역의 비상벨 설치 현황 분석, 공공안전 사각지대 탐지, 시각화 기반 인프라 확충 지원

## 🛠 전처리 개요
- 원본 형식: CSV (`안전비상벨.csv`)
- 주요 열: `X`, `Y` (EPSG:3857 기준)
- 전처리 절차:
  - 좌표 문자열 클렌징 후 숫자형으로 변환
  - EPSG:3857 → EPSG:4326 위경도 좌표계로 변환
  - 서울시 경계 Shapefile과 Spatial Join하여 서울시 영역만 필터링
  - 격자(`grid_x`, `grid_y`) 생성 및 해당 격자 내 개수 집계

## 🔁 전처리 코드 개요
- 사용 파일: `bell_grid_10m.py`
- 사용 언어: Python
- 주요 라이브러리: `pandas`, `numpy`, `geopandas`, `folium`, `pyproj`
- 처리 순서:
  1. CSV 파일 로딩 및 좌표 클렌징
  2. EPSG:3857 → EPSG:4326 변환
  3. 서울시 경계 기준 Spatial Join 수행
  4. 약 10m 단위 격자 인덱싱 및 개수 집계
  5. `bell_grid_10m.csv` 저장 및 히트맵 시각화 HTML 생성

## 📂 전처리 결과
- 저장 파일: `bell_grid_10m.csv`
- 컬럼:
  - `center_lon`: 격자 중심 경도
  - `center_lat`: 격자 중심 위도
  - `bell_count`: 해당 격자 내 비상벨 개수
- 시각화 파일: `bell_grid_10m_map.html` (Folium 기반 히트맵)

## 🏛 출처
- 데이터 출처: [SafeMap - 안전비상벨 위치 정보](https://www.safemap.go.kr/opna/data/dataView.do)
- 데이터 기준일: 2024년 12월 31일  
- Shapefile 출처: [국토정보플랫폼 - 시도/시군구 경계](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?datIde=30604&dsId=30604&pageIndex=1&pageSize=10&pageUnit=10&paginationInfo=egovframework.rte.ptl.mvc.tags.ui.pagination.PaginationInfo%40a0667c6&datPageIndex=2&datPageSize=10)

## 📌 참고 사항
- 격자 크기: EPSG:4326 기준 위도 0.00009도 (서울 기준 약 10m)
- EPSG:3857 → EPSG:4326 변환 필수, 일부 소수점 오차 존재 가능
- 서울 외 지역 데이터는 Spatial Join에서 자동 제거됨
