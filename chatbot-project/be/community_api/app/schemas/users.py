from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, Field

class UpdateMeRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=10)
    profileImageUrl: Optional[str] = None

class UpdatePasswordRequest(BaseModel):
    currentPassword: str = Field(..., min_length=1)
    newPassword: str = Field(..., min_length=8, max_length=20)

class UpdateProfileImageUrlRequest(BaseModel):
    profileImageUrl: str = Field(..., min_length=1)
