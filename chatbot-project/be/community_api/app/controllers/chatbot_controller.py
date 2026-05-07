import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .recommender_controller import get_recommendations
from dotenv import load_dotenv

load_dotenv()

# LLM 초기화. GROQ_API_KEY 환경 변수가 필요합니다.
try:
    # Llama 3.3 70B 모델은 성능이 뛰어나고 Groq에서 무료로 제공합니다.
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
except Exception:
    llm = None

def process_chat_request(user_message: str, history_dicts: list[dict]) -> str:
    if not llm:
        return "Google Gemini API 키(GOOGLE_API_KEY)가 설정되지 않아 챗봇을 사용할 수 없습니다."
        
    try:
        # 1. Single-Pass RAG: 백엔드에서 먼저 ML 모델을 돌려 추천 식당을 찾습니다. (API 소모 X)
        recs = get_recommendations(user_message)
        context_str = ""
        
        if not recs:
            context_str = "해당 조건에 맞는 추천 식당을 찾지 못했습니다."
        else:
            context_str = "다음은 내부 데이터베이스에서 찾은 추천 식당 목록입니다. 이 목록을 바탕으로 자연스럽게 답변해주세요:\n"
            for r in recs:
                context_str += f"- **{r['name']}** (주소: {r['address']}, 카테고리: {r['categories']})\n"
                if str(r['menus']).strip() and str(r['menus']).strip() != 'nan':
                    menus = str(r['menus'])[:50] + "..." if len(str(r['menus'])) > 50 else str(r['menus'])
                    context_str += f"  메뉴: {menus}\n"

        # 2. 시스템 프롬프트에 검색된 결과(Context)를 강제로 주입합니다.
        system_prompt = f"""당신은 친절한 식당 추천 챗봇입니다.
다음 규칙을 엄격히 준수하세요:
1. 식당 추천, 음식, 식당 예약과 무관한 질의가 들어오면 무조건 "저는 식당 추천 봇입니다. 죄송하지만 식당 관련 질의해 주시겠어요?" 라고 답변하세요.
2. 식당 추천 시, 반드시 아래 제공된 <추천_식당_데이터>를 기반으로만 답변하세요. 자체적인 웹 검색이나 내부 지식을 통해 식당을 임의로 지어내면 절대 안 됩니다.
3. 사용자의 요청이 모호할 경우 추가 질문(예: 가격대, 지역 등)을 하여 구체화할 수 있습니다.

<추천_식당_데이터>
{context_str}
</추천_식당_데이터>
"""
        
        chat_history = [SystemMessage(content=system_prompt)]
        for msg in history_dicts:
            if msg.get("role") == "user":
                chat_history.append(HumanMessage(content=msg.get("content", "")))
            else:
                chat_history.append(AIMessage(content=msg.get("content", "")))
                
        chat_history.append(HumanMessage(content=user_message))
        
        # 3. LLM에게 딱 1번만 질문합니다. (API 호출 1회)
        response = llm.invoke(chat_history)
        
        content = response.content
        if isinstance(content, list):
            text_blocks = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in c]
            return "\n".join(text_blocks)
        return str(content)
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        return "죄송합니다. 챗봇 처리 중 오류가 발생했습니다."
