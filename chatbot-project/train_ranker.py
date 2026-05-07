import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import os

BASE_DIR = '/Users/junwoo/chatbot-project'
SCORES_FILE = os.path.join(BASE_DIR, 'shop_scores.csv')
SHOPS_FILE = os.path.join(BASE_DIR, 'shops.csv')
MODEL_FILE = os.path.join(BASE_DIR, 'be', 'data', 'ranker_model.pkl')

print("Loading data...")
scores_df = pd.read_csv(SCORES_FILE)
shops_df = pd.read_csv(SHOPS_FILE)

# Ensure shop_id is string
scores_df['shop_id'] = scores_df['shop_id'].astype(str)
shops_df['shop_id'] = shops_df['shop_id'].astype(str)

print("Merging features...")
# Calculate shop popularity (mean score across all queries)
shop_pop = scores_df.groupby('shop_id')['score'].mean().reset_index()
shop_pop.rename(columns={'score': 'shop_popularity'}, inplace=True)

# Merge shop info into scores
df = pd.merge(scores_df, shops_df[['shop_id', 'categories', 'menus', 'address']], on='shop_id', how='left')
df = pd.merge(df, shop_pop, on='shop_id', how='left')

df['categories'] = df['categories'].fillna('')
df['menus'] = df['menus'].fillna('')
df['address'] = df['address'].fillna('')
df['search_query'] = df['search_query'].fillna('')

print("Engineering features...")
def calculate_overlap(row, text_col):
    query = str(row['search_query']).lower().replace('#', '')
    keywords = query.split()
    target_text = str(row[text_col]).lower()
    
    count = 0
    for kw in keywords:
        if kw in target_text:
            count += 1
    return count

# Vectorized equivalent for speed
# To speed up, we can use apply, but let's do it simply
def extract_features(df_to_process):
    # Vectorized text operations are faster, but apply is easier for keyword intersection
    def get_features(r):
        q = str(r['search_query']).lower().replace('#', '')
        kws = set(q.split())
        c = str(r['categories']).lower()
        m = str(r['menus']).lower()
        a = str(r['address']).lower()
        
        c_match = sum(1 for kw in kws if kw in c)
        m_match = sum(1 for kw in kws if kw in m)
        a_match = sum(1 for kw in kws if kw in a)
        
        return pd.Series([c_match, m_match, a_match, len(kws)])
        
    features = df_to_process.apply(get_features, axis=1)
    features.columns = ['cat_match', 'menu_match', 'addr_match', 'query_len']
    return features

# Process in chunks if large, but shop_scores is around 10MB, so it's manageable
feat_df = extract_features(df)
df = pd.concat([df, feat_df], axis=1)

# Target variable: We want to predict the log-based 'score'
X = df[['cat_match', 'menu_match', 'addr_match', 'query_len', 'shop_popularity']]
y = df['score']

print("Training Random Forest Ranker (Regressor)...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

preds = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, preds))
print(f"Validation RMSE: {rmse:.4f}")

# Save the model
os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
with open(MODEL_FILE, 'wb') as f:
    pickle.dump(model, f)
    
# Save shop popularity map for inference
pop_map = dict(zip(shop_pop['shop_id'], shop_pop['shop_popularity']))
with open(os.path.join(BASE_DIR, 'be', 'data', 'shop_pop.pkl'), 'wb') as f:
    pickle.dump(pop_map, f)

print(f"Model saved to {MODEL_FILE}")
