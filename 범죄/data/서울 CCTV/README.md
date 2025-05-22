# 🎥 서울시 CCTV 설치 위치 데이터 (10m 격자 기반)

## 📌 개요
- 서울시 내에 설치된 CCTV의 실제 위치 정보를 기반으로, 위경도 좌표를 약 10m 간격의 격자로 분할하여 각 격자에 존재하는 CCTV 수를 집계한 공간 밀도 데이터입니다.
- 분석 목적: CCTV 밀도 시각화, 범죄/안전 분석, 공공 감시 사각지대 탐지 및 정책 기초자료로 활용

## 🛠 전처리 개요
- 원본 형식: Excel (`seoul_cctv_locations.xlsx`)
- 주요 열: `LO`(경도), `LA`(위도)
- 전처리 절차:
  - 위도/경도 문자열에서 숫자 외 문자 제거 후 숫자형 변환
  - EPSG:4326 기준이므로 별도 좌표 변환 생략
  - 약 10m 단위로 격자 인덱스를 생성하여 위치 정규화
  - 격자별 CCTV 개수 집계 및 중심 좌표 계산

## 🔁 전처리 코드 개요
- 사용 파일: `seoul_cctv_locations_grid_10m.py`
- 사용 언어: Python
- 주요 라이브러리: `pandas`, `numpy`, `folium`
- 처리 순서:
  1. Excel 파일 로딩 및 좌표 컬럼 정제
  2. 격자 기준(`grid_x`, `grid_y`) 인덱싱
  3. `seoul_cctv_locations_grid_10m.csv`로 저장
  4. 히트맵 시각화(`seoul_cctv_locations_grid_10m_map.html`) 생성

## 📂 전처리 결과
- 저장 파일: `seoul_cctv_locations_grid_10m.csv`
- 컬럼:
  - `center_lon`: 격자 중심 경도
  - `center_lat`: 격자 중심 위도
  - `cctv_location_count`: 해당 격자 내 CCTV 개수
- 시각화 파일: `seoul_cctv_locations_grid_10m_map.html` (Folium 기반 히트맵)

## 🏛 출처
- 데이터 출처: [Bigdata Policing - 서울시 CCTV 설치 위치](https://bigdata-policing.kr/product/view?product_id=PRDT_468)
- 데이터 기준일: 2024년 3월 31일  
- Shapefile 출처: [국토정보플랫폼 - 시도/시군구 경계](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?datIde=30604&dsId=30604&pageIndex=1&pageSize=10&pageUnit=10&paginationInfo=egovframework.rte.ptl.mvc.tags.ui.pagination.PaginationInfo%40a0667c6&datPageIndex=2&datPageSize=10)

## 📌 참고 사항
- 위경도(EPSG:4326) 기준 좌표로, 서울시 평균 기준 약 10m에 해당하는 0.00009도/0.00011도 단위 격자 사용
- 행정경계 필터링은 포함되지 않았으며, 원본 CCTV 위치 전체를 기준으로 집계

