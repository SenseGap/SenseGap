import pandas as pd

# 1) April 2025 동별 생활인구 데이터 불러오기
#    파일 인코딩에 따라 'utf-8' 또는 'cp949' 중 하나만 사용하세요.
df = pd.read_csv('LOCAL_PEOPLE_DONG_202504.csv', encoding='utf-8', low_memory=False)

# 2) '행정동코드'를 8자리 문자열로 맞추기
df['행정동코드'] = df['행정동코드'].astype(int).astype(str).str.zfill(8)

# 3) 한 달간의 '총생활인구수'를 동별로 집계
summary = (
    df
    .groupby('행정동코드')['총생활인구수']
    .agg([
        ('mean_total_pop', 'mean'),
        ('std_total_pop',  'std'),
        ('min_total_pop',  'min'),
        ('max_total_pop',  'max'),
        ('median_total_pop', 'median')
    ])
    .reset_index()
)

# 4) 결과를 CSV로 저장 (utf-8-sig: 한글 깨짐 방지)
summary.to_csv('dong_population_features.csv', index=False, encoding='utf-8-sig')

# 5) 저장된 파일 확인용 출력 (옵션)
print(summary.head())
