from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Cookie
from app.routers.deps import require_user
from app.controllers import chat_controller as controller
from app.storage import db

router = APIRouter(prefix="/v1/chat", tags=["Chat"])

@router.get("/conversations")
def get_conversations(u=Depends(require_user)):
    return controller.get_my_conversations(u)

@router.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int, u=Depends(require_user)):
    return controller.get_conversation_messages(u, conversation_id)

@router.post("/conversations")
def create_conversation(payload: dict, u=Depends(require_user)):
    return controller.create_or_get_conversation(u, payload)

# WebSocket does not easily support Depends with HTTPException, so we handle auth manually
@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    sessionId = websocket.cookies.get("sessionId")
    if not sessionId:
        await websocket.close(code=1008)
        return
        
    u = db.session_user(sessionId)
    if not u:
        await websocket.close(code=1008)
        return
        
    user_id = u["userId"]
    
    try:
        await controller.handle_chat_websocket(websocket, user_id)
    except WebSocketDisconnect:
        controller.manager.disconnect(websocket, user_id)
