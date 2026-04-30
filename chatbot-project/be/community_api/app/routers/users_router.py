from fastapi import APIRouter, Depends
from app.controllers import users_controller as controller
from app.models.user import UserDict
from app.routers.deps import require_user, require_user_with_sid
from app.schemas.users import (
    UpdateMeRequest,
    UpdatePasswordRequest,
    UpdateProfileImageUrlRequest,
)

router = APIRouter(prefix="/v1/users", tags=["Users"])


@router.get("/me")
def get_me(u: UserDict = Depends(require_user)):
    return controller.get_me(u)


@router.patch("/me")
def update_me(payload: UpdateMeRequest, u: UserDict = Depends(require_user)):
    return controller.update_me(u, payload)


@router.patch("/me/password")
def update_password(payload: UpdatePasswordRequest, u: UserDict = Depends(require_user)):
    return controller.update_password(u, payload)


@router.patch("/me/profile-image-url")
def update_profile_image_url(
    payload: UpdateProfileImageUrlRequest, u: UserDict = Depends(require_user)
):
    return controller.update_profile_image_url(u, payload)


@router.delete("/me")
def delete_me(u_and_sid=Depends(require_user_with_sid)):
    return controller.delete_me(u_and_sid)


@router.get("/{user_id:int}")
def get_user(user_id: int):
    return controller.get_user(user_id)
