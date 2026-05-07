import pandas as pd
import os
import pickle

# Load data into memory once
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
SHOPS_FILE = os.path.join(BASE_DIR, 'shops.csv')
SCORES_FILE = os.path.join(BASE_DIR, 'shop_scores.csv')
MODEL_FILE = os.path.join(BASE_DIR, 'ranker_model.pkl')
SHOP_POP_FILE = os.path.join(BASE_DIR, 'shop_pop.pkl')

shops_df = pd.DataFrame()
scores_df = pd.DataFrame()
ranker_model = None
shop_pop = {}

try:
    if os.path.exists(SHOPS_FILE):
        shops_df = pd.read_csv(SHOPS_FILE)
        shops_df['shop_id'] = shops_df['shop_id'].astype(str)
        
    if os.path.exists(SCORES_FILE):
        scores_df = pd.read_csv(SCORES_FILE)
        scores_df['shop_id'] = scores_df['shop_id'].astype(str)

    if os.path.exists(MODEL_FILE):
        with open(MODEL_FILE, 'rb') as f:
            ranker_model = pickle.load(f)

    if os.path.exists(SHOP_POP_FILE):
        with open(SHOP_POP_FILE, 'rb') as f:
            shop_pop = pickle.load(f)

except Exception as e:
    print(f"Error loading recommender data: {e}")

def get_recommendations(query: str, top_k: int = 5) -> list[dict]:
    """
    Given a search query, uses ML model (Learning-to-Rank) to predict relevance.
    """
    if scores_df.empty or shops_df.empty:
        return []

    # Extract keywords
    keywords = [kw.lower() for kw in query.split()]
    
    # 1. Candidate Generation: Find rows matching any keyword
    def match_score(row_query):
        if not isinstance(row_query, str): return 0
        rq_lower = row_query.lower()
        score = 0
        for kw in keywords:
            if kw in rq_lower:
                score += 1
        return score
        
    scores_df['match_score'] = scores_df['search_query'].apply(match_score)
    candidates = scores_df[scores_df['match_score'] > 0].copy()
    
    if ranker_model and not candidates.empty:
        # 2. ML Re-Ranking
        def extract_features(row):
            shop_id = row['shop_id']
            shop_info = shops_df[shops_df['shop_id'] == shop_id]
            c = m = a = ""
            if not shop_info.empty:
                c = str(shop_info.iloc[0].get('categories', '')).lower()
                m = str(shop_info.iloc[0].get('menus', '')).lower()
                a = str(shop_info.iloc[0].get('address', '')).lower()
                
            c_match = sum(1 for kw in keywords if kw in c)
            m_match = sum(1 for kw in keywords if kw in m)
            a_match = sum(1 for kw in keywords if kw in a)
            pop = shop_pop.get(shop_id, 0)
            
            return pd.Series([c_match, m_match, a_match, len(keywords), pop])

        # extract features for candidates
        features = candidates.apply(extract_features, axis=1)
        features.columns = ['cat_match', 'menu_match', 'addr_match', 'query_len', 'shop_popularity']
        
        # predict score using trained ML model
        candidates['ml_score'] = ranker_model.predict(features)
        
        # get max score per shop and sort
        agg_scores = candidates.groupby('shop_id')['ml_score'].max().reset_index()
        top_shops = agg_scores.sort_values('ml_score', ascending=False).head(top_k)
        
        results = []
        for _, row in top_shops.iterrows():
            shop_info = shops_df[shops_df['shop_id'] == row['shop_id']]
            if not shop_info.empty:
                info = shop_info.iloc[0]
                results.append({
                    "name": info.get('shop_name', 'Unknown'),
                    "address": info.get('address', 'Unknown'),
                    "categories": info.get('categories', ''),
                    "menus": info.get('menus', '')
                })
        return results

    # 3. Fallback: Keyword search directly on shops.csv if no candidates or model missing
    def score_row(row):
        score = 0
        text = str(row.get('categories', '')) + " " + str(row.get('menus', '')) + " " + str(row.get('address', '')) + " " + str(row.get('shop_name', ''))
        for kw in keywords:
            if kw in text:
                score += 1
        return score
        
    shops_df['kw_score'] = shops_df.apply(score_row, axis=1)
    fallback_shops = shops_df[shops_df['kw_score'] > 0].sort_values('kw_score', ascending=False).head(top_k)
    
    results = []
    for _, info in fallback_shops.iterrows():
        results.append({
            "name": info.get('shop_name', 'Unknown'),
            "address": info.get('address', 'Unknown'),
            "categories": info.get('categories', ''),
            "menus": info.get('menus', '')
        })
    return results
