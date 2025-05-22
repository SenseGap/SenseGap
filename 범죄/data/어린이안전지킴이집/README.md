# 🧒 아동안전지킴이집 위치 데이터 (10m 격자 기반)

## 📌 개요
- 서울시 내 아동안전지킴이집(어린이 보호 및 범죄 예방 목적 거점)의 위치 정보를 기반으로, 약 10m 단위 격자마다 해당 시설의 존재 개수를 집계한 공간 데이터입니다.
- 분석 목적: 어린이 안전망의 공간적 분포 분석, 사각지대 탐지, 정책적 보호시설 확충 우선순위 평가 등

## 🛠 전처리 개요
- 원본 형식: CSV (`아동안전지킴이집.csv`)
- 주요 열: `X`, `Y` (EPSG:3857 기준)
- 전처리 절차:
  - 좌표 데이터에서 숫자 외 문자 제거 후 `float`으로 변환
  - EPSG:3857 → EPSG:4326 (위경도) 좌표계로 변환
  - 서울시 경계와 Spatial Join을 통해 서울시 내 시설만 필터링
  - 10m 격자(`grid_x`, `grid_y`) 기준 집계 및 중심 좌표 계산

## 🔁 전처리 코드 개요
- 사용 파일: `child_guard_grid_10m.py`
- 사용 언어: Python
- 주요 라이브러리: `pandas`, `numpy`, `geopandas`, `folium`, `pyproj`
- 처리 순서:
  1. CSV 파일 로딩 및 좌표 정제
  2. EPSG:3857 → EPSG:4326 좌표 변환
  3. 서울시 행정경계 Shapefile과 Spatial Join 수행
  4. 격자 인덱스 생성 및 시설 수 집계
  5. `child_guard_grid_10m.csv` 저장
  6. Folium 기반 시각화(`child_guard_grid_10m_map.html`) 저장

## 📂 전처리 결과
- 저장 파일: `child_guard_grid_10m.csv`
- 컬럼:
  - `center_lon`: 격자 중심 경도
  - `center_lat`: 격자 중심 위도
  - `child_guard_count`: 해당 격자 내 아동안전지킴이집 개수
- 시각화 파일: `child_guard_grid_10m_map.html` (Folium 기반 히트맵)

## 🏛 출처
- 데이터 출처: [SafeMap - 아동안전지킴이집 위치 정보](https://www.safemap.go.kr/opna/data/dataView.do)
- 데이터 기준일: 2024년 12월 31일  
- Shapefile 출처: [국토정보플랫폼 - 시도/시군구 경계](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?datIde=30604&dsId=30604&pageIndex=1&pageSize=10&pageUnit=10&paginationInfo=egovframework.rte.ptl.mvc.tags.ui.pagination.PaginationInfo%40a0667c6&datPageIndex=2&datPageSize=10)

## 📌 참고 사항
- 격자 크기는 위도 기준 약 0.00009도로 설정 (서울 기준 약 10m)
- EPSG:3857 좌표계에서 EPSG:4326으로 변환된 위경도 기준 사용
- 일부 비서울 지역 데이터는 Spatial Join 과정에서 자동 제거됨
