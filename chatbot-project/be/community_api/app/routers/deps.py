from fastapi import Cookie
from app.storage import db
from app.utils.responses import raise_http_error
from app.models.user import UserDict


def require_user(sessionId: str | None = Cookie(None)) -> UserDict:
    if not sessionId:
        raise_http_error(401, "UNAUTHORIZED")
    u = db.session_user(sessionId)
    if not u:
        raise_http_error(401, "UNAUTHORIZED")
    return u


def require_user_with_sid(sessionId: str | None = Cookie(None)) -> tuple[UserDict, str]:
    if not sessionId:
        raise_http_error(401, "UNAUTHORIZED")
    u = db.session_user(sessionId)
    if not u:
        raise_http_error(401, "UNAUTHORIZED")
    return u, sessionId
