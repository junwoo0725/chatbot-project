from fastapi.responses import JSONResponse

from app.models.user import UserDict
from app.schemas.users import (
    UpdateMeRequest,
    UpdatePasswordRequest,
    UpdateProfileImageUrlRequest,
)
from app.storage import db
from app.utils.responses import success_response, success_payload, raise_http_error
from app.utils.security import valid_password, hash_pw


def get_user(user_id: int):
    u = db.get_user(user_id)
    if not u:
        raise_http_error(404, "NOT_FOUND")

    return success_response(
        "USER_RETRIEVED",
        {
            "userId": u["userId"],
            "email": u["email"],
            "nickname": u["nickname"],
            "profileImageUrl": u.get("profileImageUrl"),
        },
    )


def get_me(u: UserDict):
    return success_response(
        "USER_RETRIEVED",
        {
            "userId": u["userId"],
            "email": u["email"],
            "nickname": u["nickname"],
            "profileImageUrl": u.get("profileImageUrl"),
        },
    )


def update_me(u: UserDict, payload: UpdateMeRequest):
    nickname = payload.nickname

    # (기존 에러코드 유지)
    if not nickname:
        raise_http_error(400, "NICKNAME_REQUIRED")
    if len(nickname) > 10:
        raise_http_error(400, "INVALID_NICKNAME")

    other = db.get_user_by_nickname(nickname)
    if other and other["userId"] != u["userId"]:
        raise_http_error(409, "NICKNAME_ALREADY_EXISTS")

    u["nickname"] = nickname
    
    # Handle Profile Image
    if payload.profileImageUrl is not None:
        url = payload.profileImageUrl
        if url and url.startswith("data:"):
            fid = db.save_file(url)
            if fid:
                url = f"/public/files/{fid}"
        
        u["profileImageUrl"] = url
        db.update_user_profile_image(u["userId"], url)

    u["updatedAt"] = db.now_iso()
    
    # DB Update (Nickname)
    db.update_user_nickname(u["userId"], nickname)
    
    return success_response("USER_UPDATED", None)


def update_password(u: UserDict, payload: UpdatePasswordRequest):
    current_pw = payload.currentPassword
    new_pw = payload.newPassword

    # 현재 비밀번호 검증
    if hash_pw(current_pw) != u["passwordHash"]:
        raise_http_error(400, "CURRENT_PASSWORD_INCORRECT")

    if not valid_password(new_pw):
        raise_http_error(400, "INVALID_PASSWORD")

    u["passwordHash"] = hash_pw(new_pw)
    u["updatedAt"] = db.now_iso()
    
    # DB Update
    db.update_user_password(u["userId"], u["passwordHash"])
    
    return success_response("PASSWORD_UPDATED", None)


def update_profile_image_url(u: UserDict, payload: UpdateProfileImageUrlRequest):
    url = payload.profileImageUrl
    if not url:
        raise_http_error(400, "BAD_REQUEST")

    if url and url.startswith("data:"):
        fid = db.save_file(url)
        if fid:
            url = f"/public/files/{fid}"

    u["profileImageUrl"] = url
    u["updatedAt"] = db.now_iso()
    
    # DB Update
    db.update_user_profile_image(u["userId"], url)

    return success_response("PROFILE_IMAGE_UPDATED", {"profileImageUrl": url})


def delete_me(u_and_sid):
    u, sid = u_and_sid

    db.delete_user(u["userId"])
    db.delete_session(sid)

    res = JSONResponse(content=success_payload("USER_DELETED", None))
    res.delete_cookie("sessionId", path="/")
    return res
