from fastapi import APIRouter, Body, Depends
from app.controllers import auth_controller as controller
from app.routers.deps import require_user, require_user_with_sid

router = APIRouter(prefix="/v1/auth", tags=["Auth"])

@router.post("/signup", status_code=201)
def signup(payload: dict = Body(...)):
    return controller.signup(payload)

@router.post("/login")
def login(payload: dict = Body(...)):
    return controller.login(payload)

@router.post("/logout")
def logout(u_and_sid=Depends(require_user_with_sid)):
    return controller.logout(u_and_sid)

@router.get("/me")
def me(u=Depends(require_user)):
    return controller.me(u)

@router.get("/availability/email")
def email_availability(email: str):
    return controller.email_availability(email)

@router.get("/availability/nickname")
def nickname_availability(nickname: str):
    return controller.nickname_availability(nickname)
