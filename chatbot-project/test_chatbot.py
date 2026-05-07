import os
import sys

# Set the API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyCFGDoPIDoNp-vCvnvrDnxwrmWKgNQjgbo"

sys.path.append('/Users/junwoo/chatbot-project/be/community_api')
from app.controllers.chatbot_controller import process_chat_request

# Test 1: In-domain recommendation request
print("=== Test 1: Recommendation Request ===")
reply1 = process_chat_request("압구정 파스타 데이트하기 좋은 식당 추천해줘", [])
print(reply1)

# Test 2: Out-of-domain request
print("\n=== Test 2: Out-of-Domain Request ===")
reply2 = process_chat_request("삼성전자 주가 어떻게 될까?", [])
print(reply2)
