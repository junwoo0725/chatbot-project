from __future__ import annotations

from typing import Optional, TypedDict

class UserDict(TypedDict):
    userId: int
    email: str
    passwordHash: str
    nickname: str
    profileImageUrl: Optional[str]
    createdAt: str
    updatedAt: str
