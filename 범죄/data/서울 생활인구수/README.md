# 👥 서울시 생활인구 데이터 (10m 격자 기반)

## 📌 개요
- 서울시에서 제공하는 시간대별 생활인구 데이터를 기반으로, 행정동 단위 인구 수치를 약 10m 단위 격자로 분할하여 격자별 인구 밀도를 추정한 공간 데이터입니다.
- 분석 목적: 지역별 인구 분포 시각화, 안전/시설/상권 분석을 위한 인구 기반 가중치 설계

## 🛠 전처리 개요
- 원본 형식: CSV (`LOCAL_PEOPLE_DONG_202504.csv`), Shapefile (`LARD_ADM_SECT_SGG_11_202505.shp`)
- 주요 열: `행정동코드`, `총생활인구수`
- 전처리 절차:
  - 인구 데이터는 시간대 구분 없이 `행정동코드`별 총합으로 집계
  - 서울시 행정동 Shapefile과 Spatial Join을 통해 행정동별 격자 추출
  - 각 행정동의 인구 수를 해당 격자 수로 나누어 격자별 인구 밀도 추정

## 🔁 전처리 코드 개요
- 사용 파일: `people_grid_10m.py`
- 사용 언어: Python
- 주요 라이브러리: `pandas`, `numpy`, `geopandas`, `folium`
- 처리 순서:
  1. 생활인구 CSV 데이터를 청크 단위로 불러오고 행정동별 합계 계산
  2. 서울시 행정동 경계 Shapefile 로딩 및 EPSG:4326으로 변환
  3. 약 10m 단위 격자 생성 및 행정동과 Spatial Join
  4. 행정동별 격자 수 계산 후 인구 수를 격자에 분배
  5. `people_grid_10m.csv` 저장 및 히트맵 시각화

## 📂 전처리 결과
- 저장 파일: `people_grid_10m.csv`
- 컬럼:
  - `center_lon`: 격자 중심 경도
  - `center_lat`: 격자 중심 위도
  - `격자_인구수`: 해당 격자에 추정된 생활인구 수
- 시각화 파일: `people_grid_10m_map.html` (Folium 기반 히트맵)

## 🏛 출처
- 데이터 출처: [서울 열린데이터광장 - 시간대별 생활인구(행정동)](https://data.seoul.go.kr/dataList/OA-14979/F/1/datasetView.do)
- 데이터 기준일: 2024년 4월 1일  
- Shapefile 출처: [국토정보플랫폼 - 시도/시군구 경계](https://www.vworld.kr/dtmk/dtmk_ntads_s002.do?datIde=30604&dsId=30604&pageIndex=1&pageSize=10&pageUnit=10&paginationInfo=egovframework.rte.ptl.mvc.tags.ui.pagination.PaginationInfo%40a0667c6&datPageIndex=2&datPageSize=10)

## 📌 참고 사항
- 시간대 구분 없이 행정동 단위 인구를 합산하여 사용
- 인구 분배는 격자 수 기준으로 단순 비례 분할됨
- 분석 목적에 따라 시간대 필터링 또는 가중치 적용 방식 수정 가능
