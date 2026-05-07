from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.controllers.chatbot_controller import process_chat_request
from app.utils.responses import success_response

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])

class MessageSchema(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class ChatRequestSchema(BaseModel):
    message: str
    history: List[MessageSchema] = []

@router.post("")
def chat_with_bot(req: ChatRequestSchema):
    try:
        # Convert Pydantic models to dict
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in req.history]
        
        reply = process_chat_request(req.message, history_dicts)
        return success_response("Chatbot response successful", {"reply": reply})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
