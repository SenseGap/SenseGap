# 📷 안심이 CCTV 위치 데이터 (10m 격자 기반)

## 📌 개요
- 서울시에서 제공하는 안심이 연계 CCTV 설치 위치 데이터를 기반으로, 약 10m 단위 격자로 분할하여 격자별 CCTV 밀도를 계산한 데이터입니다.
- 분석 목적: 특정 지역의 CCTV 설치 밀도 분석 및 사각지대 파악을 위한 시각화 및 모델 학습용 데이터로 활용

## 🛠 전처리 개요
- 원본 형식: CSV (`서울시 안심이 CCTV 연계 현황.csv`)
- 주요 열: `위도`, `경도`
- 결측치 처리: 위경도 값에 숫자 외 문자 제거 후 `NaN` 발생 시 해당 행 제거
- 좌표계: EPSG:4326 (위경도, GPS 형식)
- 10m 해상도 격자 단위로 좌표 정규화 및 CCTV 개수 집계

## 🔁 전처리 코드 개요
- 사용 파일: `cctv_grid_10m.py`
- 사용 언어: Python
- 주요 라이브러리: `pandas`, `numpy`, `folium`
- 처리 순서:
  1. CSV 파일을 인코딩 자동 판별하여 로딩
  2. 위도/경도 문자열에서 숫자 외 문자 제거 및 숫자형 변환
  3. 결측 좌표 제거
  4. 격자 단위(`grid_x`, `grid_y`) 생성 후 CCTV 개수 집계
  5. 격자 중심 좌표 계산
  6. `cctv_grid_10m.csv`로 저장 및 히트맵 시각화

## 📂 전처리 결과
- 저장 파일: `cctv_grid_10m.csv`
- 컬럼: `center_lon`, `center_lat`, `cctv_count` (격자 중심 좌표 및 CCTV 개수)
- 시각화 파일: `cctv_grid_10m_map.html` (Folium 기반 히트맵)

## 🏛 출처
- 데이터 출처: https://data.seoul.go.kr/dataList/OA-20923/S/1/datasetView.do
- Shapefile 출처: https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?datIde=30604&dsId=30604&pageIndex=1&pageSize=10&pageUnit=10&paginationInfo=egovframework.rte.ptl.mvc.tags.ui.pagination.PaginationInfo%40a0667c6&datPageIndex=2&datPageSize=10
- 데이터 기준일: 2024년 12월 31일

## 📌 참고 사항
- 격자 크기: 위도 방향 약 0.00009도, 경도 방향 약 0.00011도 (서울 기준 약 10m)
- 좌표계 변환은 수행하지 않았으며, 원본 데이터가 EPSG:4326으로 가정됨
