# 🚓 치안시설 위치 데이터 (10m 격자 기반)

## 📌 개요
- 경찰서, 지구대, 파출소 등 치안시설의 위치 정보를 기반으로, 서울시 영역을 약 10m 단위 격자로 분할하여 격자별 치안시설 개수를 집계한 공간 데이터입니다.
- 분석 목적: 지역별 치안 인프라의 공간 밀도 분석 및 사각지대 탐지를 위한 기초 자료로 활용

## 🛠 전처리 개요
- 원본 형식: CSV (`치안시설.csv`)
- 주요 열: `X`, `Y` (EPSG:3857 좌표계 기반)
- 전처리 절차:
  - 좌표 문자열에서 숫자 외 문자 제거 후 숫자형 변환
  - EPSG:3857 → EPSG:4326 (위경도)로 좌표 변환
  - 서울시 경계와 Spatial Join하여 서울 지역 내 시설만 필터링
  - 약 10m 간격의 격자 기준으로 위치 정규화 및 개수 집계

## 🔁 전처리 코드 개요
- 사용 파일: `police_grid_10m.py`
- 사용 언어: Python
- 주요 라이브러리: `pandas`, `numpy`, `geopandas`, `folium`, `pyproj`
- 처리 순서:
  1. CSV 파일 로드 및 좌표 클렌징
  2. EPSG:3857에서 EPSG:4326으로 좌표 변환
  3. 서울시 경계와 Spatial Join
  4. 격자 인덱스(`grid_x`, `grid_y`) 생성
  5. 격자별 치안시설 수 집계 및 중심 좌표 계산
  6. `police_grid_10m.csv` 저장 및 히트맵 시각화

## 📂 전처리 결과
- 저장 파일: `police_grid_10m.csv`
- 컬럼:
  - `center_lon`: 격자 중심 경도
  - `center_lat`: 격자 중심 위도
  - `police_count`: 해당 격자 내 치안시설 개수
- 시각화 파일: `police_grid_10m_map.html` (Folium 기반 히트맵)

## 🏛 출처
- 데이터 출처: [SafeMap - 치안시설 위치 정보](https://www.safemap.go.kr/opna/data/dataView.do)
- 데이터 기준일: 2024년 12월 31일  
- Shapefile 출처: [국토정보플랫폼 - 시도/시군구 경계](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?datIde=30604&dsId=30604&pageIndex=1&pageSize=10&pageUnit=10&paginationInfo=egovframework.rte.ptl.mvc.tags.ui.pagination.PaginationInfo%40a0667c6&datPageIndex=2&datPageSize=10)

## 📌 참고 사항
- 원본 좌표계가 EPSG:3857이므로 위경도 기반 분석을 위해 좌표 변환 필수
- 좌표 변환 과정에서 미세한 오차 발생 가능
- 격자 단위는 EPSG:4326 기준 위도 0.00009도(약 10m)에 해당

