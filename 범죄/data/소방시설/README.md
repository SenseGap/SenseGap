# 🔥 소방시설 위치 데이터 (10m 격자 기반)

## 📌 개요
- 전국 소방시설(소화전, 비상소화장치함 등) 위치 데이터를 기반으로 서울시 영역 내에서 약 10m 단위 격자로 나누어 격자별 소방시설 개수를 집계한 데이터입니다.
- 분석 목적: 화재 대응 인프라의 공간적 밀도 분석, 안전 사각지대 탐지 및 시각화

## 🛠 전처리 개요
- 원본 형식: CSV (`소방시설.csv`)
- 주요 열: `X`, `Y` (EPSG:3857 기준)
- 좌표계 변환: EPSG:3857 → EPSG:4326 (위경도)
- 결측치 처리: 좌표 문자열 중 숫자 외 문자 제거 후 변환, NaN 발생 시 해당 행 제거
- 서울시 경계 기준 Spatial Join 수행 (비서울 지역 필터링)
- 10m 해상도 격자 기준으로 위치 정규화 후 격자별 시설 개수 집계

## 🔁 전처리 코드 개요
- 사용 파일: `fire_grid_10m.py`
- 사용 언어: Python
- 주요 라이브러리: `pandas`, `numpy`, `geopandas`, `folium`, `pyproj`
- 처리 순서:
  1. CSV 파일 로딩 및 좌표 문자열 정제
  2. EPSG:3857 → EPSG:4326 좌표계 변환
  3. 서울시 경계 Shapefile과 Spatial Join으로 서울시 내 시설만 필터링
  4. 약 10m 해상도 격자 생성 및 `grid_x`, `grid_y` 단위로 집계
  5. 격자 중심 좌표 계산 및 `fire_grid_10m.csv` 저장
  6. 히트맵 시각화 파일(`fire_grid_10m_map.html`) 생성

## 📂 전처리 결과
- 저장 파일: `fire_grid_10m.csv`
- 컬럼:
  - `center_lon`: 격자 중심 경도
  - `center_lat`: 격자 중심 위도
  - `fire_count`: 해당 격자 내 소방시설 개수
- 시각화 파일: `fire_grid_10m_map.html` (Folium 기반 히트맵)

## 🏛 출처
- 데이터 출처: [SafeMap - 소방시설 위치 정보](https://www.safemap.go.kr/opna/data/dataView.do)
- 데이터 기준일: 2024년 12월 31일  
- Shapefile 출처: [국토정보플랫폼 - 시도/시군구 경계](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?datIde=30604&dsId=30604&pageIndex=1&pageSize=10&pageUnit=10&paginationInfo=egovframework.rte.ptl.mvc.tags.ui.pagination.PaginationInfo%40a0667c6&datPageIndex=2&datPageSize=10)

## 📌 참고 사항
- 소방시설 위치는 UTM 기반 EPSG:3857 좌표로 제공되며, 위경도 변환이 필수
- 좌표계 변환 시 일부 소수점 오차 발생 가능
- 격자 크기 기준: 약 0.00009도(위도), 서울 기준 약 10m
