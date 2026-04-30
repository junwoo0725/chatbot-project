from fastapi import FastAPI

from app.routers.auth_router import router as auth_router
from app.routers.users_router import router as users_router
from app.routers.posts_router import router as posts_router
from app.routers.public_router import router as public_router
from app.routers.upload_router import router as upload_router
from app.routers.chat_router import router as chat_router

def register_routers(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(posts_router)
    app.include_router(public_router)
    app.include_router(upload_router, prefix="/upload", tags=["Upload"])
    app.include_router(chat_router)
