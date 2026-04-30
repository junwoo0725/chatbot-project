from fastapi.responses import JSONResponse
from app.storage import db
from app.utils.responses import success_response, success_payload, raise_http_error
from app.utils.security import valid_email, valid_password, hash_pw

COOKIE_KW = dict(
    key="sessionId",
    httponly=True,
    samesite="lax",
    secure=False,
    path="/",
)

def signup(payload: dict):
    email = payload.get("email")
    password = payload.get("password")
    password_confirm = payload.get("passwordConfirm")
    nickname = payload.get("nickname")
    profile_url = payload.get("profileImageUrl")

    if not email:
        raise_http_error(400, "EMAIL_REQUIRED")
    if not password:
        raise_http_error(400, "PASSWORD_REQUIRED")
    if password != password_confirm:
        raise_http_error(400, "PASSWORD_CONFIRM_MISMATCH")
    if not nickname:
        raise_http_error(400, "NICKNAME_REQUIRED")

    if not valid_email(email):
        raise_http_error(400, "INVALID_EMAIL")
    if not valid_password(password):
        raise_http_error(400, "INVALID_PASSWORD")
    if len(nickname) > 10:
        raise_http_error(400, "INVALID_NICKNAME")

    if db.get_user_by_email(email):
        raise_http_error(409, "EMAIL_ALREADY_EXISTS")
    if db.get_user_by_nickname(nickname):
        raise_http_error(409, "NICKNAME_ALREADY_EXISTS")

    if profile_url and profile_url.startswith("data:"):
        fid = db.save_file(profile_url)
        if fid:
            profile_url = f"/public/files/{fid}"

    db.create_user(email, hash_pw(password), nickname, profile_url)

    return success_response("SIGNUP_SUCCESS", None, http_status=201)

def login(payload: dict):
    email = payload.get("email")
    password = payload.get("password")
    if not email:
        raise_http_error(400, "EMAIL_REQUIRED")
    if not password:
        raise_http_error(400, "PASSWORD_REQUIRED")

    u = db.get_user_by_email(email)
    if not u:
        raise_http_error(404, "USER_NOT_FOUND")
    if u["passwordHash"] != hash_pw(password):
        raise_http_error(401, "PASSWORD_INCORRECT")

    sid = db.create_session(u["userId"])

    res = JSONResponse(content=success_payload("LOGIN_SUCCESS", {
        "user": {
            "userId": u["userId"],
            "email": u["email"],
            "nickname": u["nickname"],
            "profileImageUrl": u.get("profileImageUrl"),
        }
    }))
    res.set_cookie(value=sid, **COOKIE_KW)
    return res

def logout(u_and_sid):
    _, sid = u_and_sid
    db.delete_session(sid)

    res = JSONResponse(content=success_payload("LOGOUT_SUCCESS", None))
    res.delete_cookie("sessionId", path="/")
    return res

def me(u):
    return success_response("USER_RETRIEVED", {
        "userId": u["userId"],
        "email": u["email"],
        "nickname": u["nickname"],
        "profileImageUrl": u.get("profileImageUrl"),
    })

def email_availability(email: str):
    return success_response("EMAIL_AVAILABLE", {"available": db.get_user_by_email(email) is None})

def nickname_availability(nickname: str):
    return success_response("NICKNAME_AVAILABLE", {"available": db.get_user_by_nickname(nickname) is None})

