import sys
import os

sys.path.append('/Users/junwoo/chatbot-project/be/community_api')
from app.controllers.recommender_controller import get_recommendations

query1 = "압구정 데이트 파스타"
print(f"Query: {query1}")
recs1 = get_recommendations(query1)
for r in recs1:
    print(r['name'], r['address'])

query2 = "중구 평양냉면"
print(f"\\nQuery: {query2}")
recs2 = get_recommendations(query2)
for r in recs2:
    print(r['name'], r['address'])
