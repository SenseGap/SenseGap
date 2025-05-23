import pandas as pd

# 1) 소방서별 취약자 정보 로드
vuln_df = pd.read_csv('서울시 소방서별 재난안전 취약자 정보.csv', encoding='cp949')

# (a) RRPOP: 전체 등록인구
#     SNR_POP, BBY_POP, DSB_POP, OPH: 취약계층 수
vuln_df['senior_ratio']   = vuln_df['SNR_POP'] / vuln_df['RRPOP']
vuln_df['baby_ratio']     = vuln_df['BBY_POP'] / vuln_df['RRPOP']
vuln_df['disabled_ratio'] = vuln_df['DSB_POP'] / vuln_df['RRPOP']
vuln_df['onep_ratio']     = vuln_df['OPH']     / vuln_df['RRPOP']

# (b) SoVI / Cutter et al. 기반 factor loadings (예시값)
loadings = {
    'disabled': 0.48,
    'senior':   0.42,
    'baby':     0.35,
    'onep':     0.30
}
total = sum(loadings.values())
weights = {k: v/total for k,v in loadings.items()}

# (c) station-level vuln_index 계산
vuln_df['station_vuln_raw'] = (
      weights['disabled'] * vuln_df['disabled_ratio']
    + weights['senior']   * vuln_df['senior_ratio']
    + weights['baby']     * vuln_df['baby_ratio']
    + weights['onep']     * vuln_df['onep_ratio']
)
minv, maxv = vuln_df['station_vuln_raw'].min(), vuln_df['station_vuln_raw'].max()
vuln_df['station_vuln_index'] = (
    (vuln_df['station_vuln_raw'] - minv) / (maxv - minv)
)

# 인덱스로 lookup 편하게
vuln_df = vuln_df.rename(columns={'FRSTT_NM':'fire_station'}).set_index('fire_station')

# 2) 격자 데이터 로드
grid_df = pd.read_csv('checkpoint1Dataset.csv', encoding='utf-8')
# service_name, area_ratio 는 문자열로
grid_df['service_name'] = grid_df['service_name'].astype(str)
grid_df['area_ratio']   = grid_df['area_ratio'].astype(str)

# 3) 소방서–안전센터 매핑 (필요 시)
mapping_df = pd.read_csv('소방서 안전센터 관할정보.csv', encoding='utf-8')
mapping_df.columns = ['fire_station','safety_center']

# 4) 금천→구로 등 예외 매핑
override_map = {'금천소방서':'구로소방서'}

# 5) 격자별 vuln 가중합 함수
def grid_vuln(row):
    names  = [n.strip() for n in row['service_name'].split(';')]
    ratios = [float(r)  for r in row['area_ratio'].split(';')]
    s = 0.0
    for name, r in zip(names, ratios):
        # override 우선
        if name in override_map:
            station = override_map[name]
        elif name in vuln_df.index:
            station = name
        else:
            # 안전센터명 → 소방서명 매핑
            m = mapping_df.loc[mapping_df['safety_center']==name, 'fire_station']
            station = m.iloc[0] if not m.empty else None

        # override on mapped
        if station in override_map:
            station = override_map[station]

        if station not in vuln_df.index:
            continue

        s += vuln_df.at[station,'station_vuln_index'] * r

    return s

# 6) 함수 적용
grid_df['grid_vuln_index'] = grid_df.apply(grid_vuln, axis=1)

# 7) 저장
grid_df.to_csv('grid_with_vuln_index.csv', index=False, encoding='utf-8-sig')
print("✔ grid_with_vuln_index.csv 생성 완료")
