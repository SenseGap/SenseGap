import pandas as pd

# 1) 원본 격자 데이터 읽기
grid_df = pd.read_csv('checkpoint1Dataset.csv', encoding='utf-8')
grid_df['service_name'] = grid_df['service_name'].astype(str)
grid_df['area_ratio']   = grid_df['area_ratio'].astype(str)

# 2) 소방서–안전센터 매핑 읽기
mapping_df = pd.read_csv('소방서 안전센터 관할정보.csv', encoding='utf-8')
mapping_df.columns = ['fire_station', 'safety_center']

# 3) 소방서별 취약자 정보 읽기
vuln_df = pd.read_csv('서울시 소방서별 재난안전 취약자 정보.csv', encoding='cp949')
vuln_df = vuln_df.rename(columns={'FRSTT_NM':'fire_station'}).set_index('fire_station')

# 4) 대체 매핑: 금천 → 구로 외에 필요 시 추가
override_map = {
    '금천소방서': '구로소방서',
}

# 5) 계산할 지표 리스트
cols = ['FFOFCR_CHR', 'SNR_POP', 'BBY_POP', 'DSB_POP', 'OPH']

def weighted_vuln(row):
    names  = [n.strip() for n in row['service_name'].split(';')]
    ratios = [float(x)     for x in row['area_ratio'].split(';')]
    acc = {c: 0.0 for c in cols}

    for name, r in zip(names, ratios):
        # 1) 우선 name 자체가 override 대상인지 확인
        if name in override_map:
            station = override_map[name]
        # 2) vuln_df에 직접 있는 소방서명인지 확인
        elif name in vuln_df.index:
            station = name
        # 3) 안전센터명이면 매핑해서 상위 소방서 찾기
        else:
            matched = mapping_df.loc[mapping_df['safety_center'] == name, 'fire_station']
            if matched.empty:
                continue
            station = matched.iloc[0]

        # 4) 매핑된 station에도 override_map을 적용
        station = override_map.get(station, station)

        # 5) 최종적으로 vuln_df에 있어야 가중합 수행
        if station not in vuln_df.index:
            continue

        # 6) 지표값 가중합
        for c in cols:
            acc[c] += vuln_df.at[station, c] * r

    return pd.Series(acc)

# 7) 적용 및 저장
vuln_weighted = grid_df.apply(weighted_vuln, axis=1)
result_df = pd.concat([grid_df, vuln_weighted], axis=1)
result_df.to_csv('grid_with_vulnerable_info.csv', index=False, encoding='utf-8-sig')
print("✔ grid_with_vulnerable_info.csv 생성 완료")
