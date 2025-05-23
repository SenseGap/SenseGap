import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture

# 1) 데이터 로드
df = pd.read_csv("tempDataset.csv")

# 컬럼명 오타 수정
if "gird_dispatch_count_total" in df.columns:
    df.rename(columns={"gird_dispatch_count_total": "grid_dispatch_count_total"}, inplace=True)

# 2) 사용할 피처만 선택
features = ["road_travel_time_s", "grid_dispatch_count_total", "fire_risk_score"]
X = df[features].values

# 3) 스케일링 (평균0, 분산1)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4) BIC 기준 최적 GMM 탐색
best_bic = np.inf
best_gmm = None
best_k   = None

for k in range(1, 11):
    gmm = GaussianMixture(
        n_components=k,
        covariance_type="full",
        random_state=42,
        n_init=5
    )
    gmm.fit(X_scaled)
    bic = gmm.bic(X_scaled)
    if bic < best_bic:
        best_bic = bic
        best_gmm = gmm
        best_k   = k

print(f"최적 클러스터 수 = {best_k}, BIC = {best_bic:.2f}")

# 5) 최적 GMM으로 클러스터 할당 및 소속 확률 계산
labels = best_gmm.predict(X_scaled)          # 0…best_k-1
probs  = best_gmm.predict_proba(X_scaled)
max_p  = probs.max(axis=1)

# 6) 결과를 DataFrame에 추가
df["infra_grade"]     = labels + 1          # 등급을 1부터 시작
df["infra_certainty"] = max_p

# 7) 결과 저장
df.to_csv("clustered_infra_simple_gmm.csv", index=False, encoding="utf-8")
print("✅ clustered_infra_simple_gmm.csv 저장 완료")
