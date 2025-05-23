import pandas as pd

# 1) 그리드 읽기
grid_df = pd.read_csv('gridRoadTimeFixed.csv', encoding='utf-8-sig')

# 2) 안전센터별 구급차 수 (서울만)
try:
    center_raw = pd.read_csv(
        '소방청_전국 소방서 및 119안전센터별 구급차 정보_20231231.csv',
        encoding='utf-8-sig'
    )
except UnicodeDecodeError:
    center_raw = pd.read_csv(
        '소방청_전국 소방서 및 119안전센터별 구급차 정보_20231231.csv',
        encoding='latin1'
    )

# 서울만 필터
center_raw = center_raw[center_raw['시도'] == '서울'].copy()

# 컬럼명 표준화
center_raw.rename(columns={
    '센터': 'center_name',
    '소방서': 'station_name',
    '수량': 'amb_count'
}, inplace=True)
center_raw['amb_count'] = pd.to_numeric(center_raw['amb_count'], errors='coerce').fillna(0)

# 센터→구급차 수, 센터→소방서명 맵
map_center_amb     = center_raw.groupby('center_name')['amb_count'].sum().to_dict()
map_center2station = center_raw.groupby('center_name')['station_name'].first().to_dict()


# 3) 소방서별 장비 정보
equip_raw = pd.read_csv(
    '소방장비(2017년+이후)_20250518193614.csv',
    encoding='utf-8-sig',
    skiprows=2
)
equip = equip_raw.iloc[2:].copy()
equip.rename(columns={equip_raw.columns[1]: 'station_name'}, inplace=True)

# 총장비(C열)와 구급차(AF열)
equip['total_eq'] = pd.to_numeric(equip[equip.columns[2]], errors='coerce').fillna(0)
equip['amb_eq']   = pd.to_numeric(equip['구급차'], errors='coerce').fillna(0)

map_station_total = equip.set_index('station_name')['total_eq'].to_dict()
map_station_amb   = equip.set_index('station_name')['amb_eq'].to_dict()


# 4) 그리드별 DPLYD_AMB, DPLYD_FRE 계산
dplyd_amb = []
dplyd_fre = []

for _, r in grid_df.iterrows():
    services = str(r['service_name']).split(';')
    ratios   = [float(x) for x in str(r['area_ratio']).split(';')]

    sum_amb = 0.0
    sum_fre = 0.0

    for svc, ratio in zip(services, ratios):
        if svc in map_center_amb:
            # 센터 매칭
            cen_amb = map_center_amb[svc]
            st_name = map_center2station[svc]
            st_amb  = map_station_amb.get(st_name, 0)
            st_tot  = map_station_total.get(st_name, 0)
        else:
            # 센터가 아니면, service_name을 소방서명으로 간주
            cen_amb = 0
            st_name = svc
            st_amb  = map_station_amb.get(st_name, 0)
            st_tot  = map_station_total.get(st_name, 0)

        st_fre = max(st_tot - st_amb, 0)

        sum_amb += ratio * (cen_amb + st_amb)
        sum_fre += ratio * st_fre

    dplyd_amb.append(sum_amb)
    dplyd_fre.append(sum_fre)

grid_df['DPLYD_AMB'] = dplyd_amb
grid_df['DPLYD_FRE'] = dplyd_fre

# 5) 결과 저장
grid_df.to_csv('gridRoadTimeDeployedStatus.csv', index=False, encoding='utf-8-sig')
