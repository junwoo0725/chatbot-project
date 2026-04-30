from fastapi import APIRouter, Body, Depends
from app.controllers import posts_controller as controller
from app.routers.deps import require_user

router = APIRouter(prefix="/v1/posts", tags=["Posts"])

@router.get("")
def list_posts(offset: int = 0, limit: int = 10):
    return controller.list_posts(offset, limit)

@router.get("/{post_id:int}")
def get_post(post_id: int):
    return controller.get_post(post_id)

@router.post("", status_code=201)
def create_post(payload: dict = Body(...), u=Depends(require_user)):
    return controller.create_post(u, payload)

@router.patch("/{post_id:int}")
def update_post(post_id: int, payload: dict = Body(...), u=Depends(require_user)):
    return controller.update_post(u, post_id, payload)

@router.delete("/{post_id:int}")
def delete_post(post_id: int, u=Depends(require_user)):
    return controller.delete_post(u, post_id)

@router.post("/{post_id:int}/likes", status_code=201)
def like_post(post_id: int, u=Depends(require_user)):
    return controller.like_post(u, post_id)

@router.delete("/{post_id:int}/likes")
def unlike_post(post_id: int, u=Depends(require_user)):
    return controller.unlike_post(u, post_id)

@router.get("/{post_id:int}/comments")
def list_comments(post_id: int):
    return controller.list_comments(post_id)

@router.post("/{post_id:int}/comments", status_code=201)
def create_comment(post_id: int, payload: dict = Body(...), u=Depends(require_user)):
    return controller.create_comment(u, post_id, payload)

@router.patch("/{post_id:int}/comments/{comment_id:int}")
def update_comment(post_id: int, comment_id: int, payload: dict = Body(...), u=Depends(require_user)):
    return controller.update_comment(u, post_id, comment_id, payload)

@router.delete("/{post_id:int}/comments/{comment_id:int}")
def delete_comment(post_id: int, comment_id: int, u=Depends(require_user)):
    return controller.delete_comment(u, post_id, comment_id)
