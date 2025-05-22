# 🧯 5대범죄발생현황

## 📌 개요
- 서울시 자치구별 5대 범죄(살인, 강도, 성폭력, 절도, 폭력) 발생 현황 데이터를 기반으로, 약 10m 단위 격자로 분할하여 격자별 범죄 건수를 계산한 데이터입니다.
- 분석 목적: CCTV 또는 안전 인프라 설치의 우선순위를 판단하기 위한 공간적 위험도 지표로 활용

## 🛠 전처리 개요
- 원본 형식: CSV (`5대범죄발생현황_20250510150209.csv`)
- 주요 열: `자치구`, `소계_발생`
- 불필요한 행 제거: `구분1`이 `'합계'`, `자치구`가 `'소계'`인 경우 제거
- 결측치 처리: 발생 건수를 숫자형으로 변환하고 `NaN`은 0으로 대체
- 공간 데이터 기준 좌표계: EPSG:4326 (위경도)
- 좌표 기반 10m 격자 생성 및 자치구 경계와 Spatial Join 수행

## 🔁 전처리 코드 개요
- 사용 파일: `crime_grid_10m.py`
- 사용 언어: Python
- 주요 라이브러리: `pandas`, `numpy`, `geopandas`, `folium`
- 처리 순서:
  1. 자치구 경계 Shapefile(`LARD_ADM_SECT_SGG_11_202505.shp`) 불러오기 및 정리
  2. 범죄 통계 CSV 헤더 전처리 및 자치구별 소계(발생 건수) 추출
  3. 서울시 전체 범위에 대해 약 10m 격자 생성
  4. 격자와 자치구 경계를 Spatial Join하여 각 격자가 속한 자치구 식별
  5. 자치구별 격자 수를 계산하여, 발생 건수를 격자 단위로 분배
  6. 최종적으로 `crime_grid_10m.csv`와 시각화 HTML 저장

## 📂 전처리 결과
- 저장 파일: `crime_grid_10m.csv`
- 컬럼: `center_lon`, `center_lat`, `전체_격자` (각 격자의 위도, 경도, 해당 격자 내 범죄 건수 추정치)
- 시각화 파일: `crime_grid_10m_map.html` (Folium 기반 히트맵)

## 🏛 출처
- 데이터 출처: https://data.seoul.go.kr/dataList/316/S/2/datasetView.do
- Shapefile 출처: https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?datIde=30604&dsId=30604&pageIndex=1&pageSize=10&pageUnit=10&paginationInfo=egovframework.rte.ptl.mvc.tags.ui.pagination.PaginationInfo%40a0667c6&datPageIndex=2&datPageSize=10
- 데이터 기준일: 2025년 5월 10일

## 📌 참고 사항
- 자치구명 불일치로 인한 누락이 일부 존재할 수 있음
- 격자 크기(0.00009도)는 위경도 기준 약 10m에 해당

