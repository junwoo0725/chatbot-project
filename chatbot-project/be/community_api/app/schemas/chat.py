from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    is_read: bool
    created_at: datetime

class ConversationResponse(BaseModel):
    id: int
    other_user_id: int
    other_user_nickname: str
    other_user_profile: Optional[str]
    last_message: Optional[str]
    last_message_at: Optional[datetime]
    unread_count: int

class ConversationCreateRequest(BaseModel):
    other_user_id: int
