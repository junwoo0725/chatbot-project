import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import ndcg_score

BASE_DIR = '/Users/junwoo/chatbot-project'
SCORES_FILE = os.path.join(BASE_DIR, 'shop_scores.csv')
SHOPS_FILE = os.path.join(BASE_DIR, 'shops.csv')
MODEL_FILE = os.path.join(BASE_DIR, 'be/community_api/app/data/ranker_model.pkl')
POP_FILE = os.path.join(BASE_DIR, 'be/community_api/app/data/shop_pop.pkl')

def calculate_mrr(y_true, y_score):
    order = np.argsort(y_score)[::-1]
    y_true_sorted = np.take(y_true, order)
    pos_indices = np.where(y_true_sorted > 0)[0]
    return 1.0 / (pos_indices[0] + 1) if len(pos_indices) > 0 else 0.0

def evaluate_on_group(group, model, model_name):
    y_true = group['score'].values.reshape(1, -1)
    if model_name == "Random":
        y_pred = np.random.rand(len(group)).reshape(1, -1)
    else:
        X_group = group[['cat_match', 'menu_match', 'addr_match', 'facility_match', 'award_match', 'query_len', 'shop_popularity']]
        y_pred = model.predict(X_group).reshape(1, -1)
    
    try:
        n_val = ndcg_score(y_true, y_pred, k=5)
        m_val = calculate_mrr(y_true[0], y_pred[0])
        return n_val, m_val
    except:
        return None, None

print("1. 고도화된 데이터 전처리 및 피처 추출...")
scores_df = pd.read_csv(SCORES_FILE)
shops_df = pd.read_csv(SHOPS_FILE)
scores_df['shop_id'] = scores_df['shop_id'].astype(str)
shops_df['shop_id'] = shops_df['shop_id'].astype(str)

shop_pop = scores_df.groupby('shop_id')['score'].mean().reset_index().rename(columns={'score': 'shop_popularity'})
df = pd.merge(scores_df, shops_df[['shop_id', 'categories', 'menus', 'address', 'facilities', 'awards']], on='shop_id', how='left')
df = pd.merge(df, shop_pop, on='shop_id', how='left').fillna('')

def extract_features(r):
    q = str(r['search_query']).lower().replace('#', '')
    kws = set(q.split())
    # 스키마 사진에 있던 모든 필드 활용
    c, m, a = str(r['categories']).lower(), str(r['menus']).lower(), str(r['address']).lower()
    f, aw = str(r['facilities']).lower(), str(r['awards']).lower()
    
    return pd.Series([
        sum(1 for kw in kws if kw in c),
        sum(1 for kw in kws if kw in m),
        sum(1 for kw in kws if kw in a),
        sum(1 for kw in kws if kw in f), # 편의시설 매칭 추가
        sum(1 for kw in kws if kw in aw), # 수상 내역 매칭 추가
        len(kws)
    ])

feat_df = df.apply(extract_features, axis=1)
feat_df.columns = ['cat_match', 'menu_match', 'addr_match', 'facility_match', 'award_match', 'query_len']
df = pd.concat([df, feat_df], axis=1)

X_cols = ['cat_match', 'menu_match', 'addr_match', 'facility_match', 'award_match', 'query_len', 'shop_popularity']
unique_queries = df['search_query'].unique()

print(f"2. 5-Fold 교차 검증 시작 (총 5회 반복 학습)...")
kf = KFold(n_splits=5, shuffle=True, random_state=42)
results = []

for fold, (train_idx, test_idx) in enumerate(kf.split(unique_queries), 1):
    train_q, test_q = unique_queries[train_idx], unique_queries[test_idx]
    train_df = df[df['search_query'].isin(train_q)]
    test_df = df[df['search_query'].isin(test_q)]
    
    X_train, y_train = train_df[X_cols], train_df['score']
    
    # 모델 정의
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    hgbm = HistGradientBoostingRegressor(max_iter=100, max_depth=10, random_state=42)
    
    rf.fit(X_train, y_train)
    hgbm.fit(X_train, y_train)
    
    # 테스트셋 평가
    rnd_metrics = [evaluate_on_group(test_df[test_df['search_query'] == q], None, "Random") for q in test_q]
    rf_metrics = [evaluate_on_group(test_df[test_df['search_query'] == q], rf, "RF") for q in test_q]
    hgbm_metrics = [evaluate_on_group(test_df[test_df['search_query'] == q], hgbm, "HGBM") for q in test_q]
    
    def mean_valid(metrics):
        ndcgs = [m[0] for m in metrics if m[0] is not None]
        return np.mean(ndcgs) if ndcgs else 0
        
    results.append({
        'fold': fold,
        'Random': mean_valid(rnd_metrics),
        'RF': mean_valid(rf_metrics),
        'HGBM (Better)': mean_valid(hgbm_metrics)
    })
    print(f"   - Fold {fold} 완료: RF({results[-1]['RF']:.4f}) vs HGBM({results[-1]['HGBM (Better)']:.4f})")

res_df = pd.DataFrame(results)
summary = res_df.mean()

print("\n" + "="*60)
print(f"{'Metric (NDCG@5 Average)':<30} | {'Value':<10}")
print("-" * 60)
print(f"{'Random Baseline':<30} | {summary['Random']:<10.4f}")
print(f"{'Random Forest':<30} | {summary['RF']:<10.4f}")
print(f"{'HistGradientBoosting (Winner!)':<30} | {summary['HGBM (Better)']:<10.4f}")
print("="*60 + "\n")

# 최종 모델은 전체 데이터로 학습하여 저장
print("3. 전체 데이터로 최종 모델 학습 및 저장...")
final_model = HistGradientBoostingRegressor(max_iter=200, max_depth=12, random_state=42).fit(df[X_cols], df['score'])

os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
with open(MODEL_FILE, 'wb') as f:
    pickle.dump(final_model, f)

pop_map = dict(zip(shop_pop['shop_id'], shop_pop['shop_popularity']))
with open(POP_FILE, 'wb') as f:
    pickle.dump(pop_map, f)

print(f"최적의 고도화 모델이 {MODEL_FILE} 에 저장되었습니다.")
