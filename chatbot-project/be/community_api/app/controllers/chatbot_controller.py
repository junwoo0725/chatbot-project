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
            context_str = "다음은 내부 머신러닝 모델(Random Forest)이 사용자 로그를 분석하여 산출한 점수(ML Score)가 높은 순서대로 나열된 추천 식당 목록입니다. 1위가 가장 적합한 식당입니다:\n"
            for r in recs:
                context_str += f"{r['rank']}위. **{r['name']}** (추천 점수: {r['score']}, 주소: {r['address']}, 카테고리: {r['categories']})\n"
                if str(r['menus']).strip() and str(r['menus']).strip() != 'nan':
                    menus = str(r['menus'])[:50] + "..." if len(str(r['menus'])) > 50 else str(r['menus'])
                    context_str += f"   - 메뉴: {menus}\n"

        # 2. 시스템 프롬프트에 검색된 결과(Context)를 강제로 주입합니다.
        system_prompt = f"""당신은 사용자 행동 로그를 학습한 머신러닝 기반 식당 추천 전문가입니다.
다음 규칙을 엄격히 준수하세요:
1. 식당 추천, 음식, 식당 예약과 무관한 질의가 들어오면 무조건 "저는 식당 추천 봇입니다. 죄송하지만 식당 관련 질의해 주시겠어요?" 라고 답변하세요.
2. 아래 제공된 <추천_식당_데이터>는 이미 내부 머신러닝 모델에 의해 최적의 순서로 정렬된 데이터입니다.
3. 답변 시 "추천 점수", "ML 스코어", "랭킹 몇 위"와 같은 기술적인 용어는 절대 언급하지 마세요. 
4. 대신, 제공된 순서가 가장 좋은 식당들이므로 이를 바탕으로 사용자에게 아주 자연스럽고 친절하게 식당을 추천해 주세요. (예: "가장 먼저 추천해드리고 싶은 곳은 ~입니다", "다음으로 ~도 인기가 많습니다" 등)
5. 반드시 제공된 데이터로만 답변하고, 식당을 지어내지 마세요.

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
