from app.storage import db
from app.utils.responses import success_response, raise_http_error


def list_posts(offset: int, limit: int):
    items = db.list_posts(offset, limit)
    return success_response("POSTS_RETRIEVED", {"items": items})


def get_post(post_id: int):
    p = db.get_post(post_id, increase_hits=True)
    if not p:
        raise_http_error(404, "NOT_FOUND")
    return success_response("POST_RETRIEVED", p)


def create_post(u, payload: dict):
    title = payload.get("title")
    content = payload.get("content")
    file_url = payload.get("fileUrl")

    if not title:
        raise_http_error(400, "TITLE_REQUIRED")
    if len(title) > 26:
        raise_http_error(400, "TITLE_TOO_LONG")
    if not content:
        raise_http_error(400, "CONTENT_REQUIRED")

    real_file_url = None
    if file_url and file_url.startswith("data:"):
        fid = db.save_file(file_url)
        if fid:
            real_file_url = f"/public/files/{fid}"
    else:
        real_file_url = file_url

    p = db.create_post(title=title, content=content, author_user_id=u["userId"], file_url=real_file_url)
    return success_response("POST_CREATED", {"postId": p["postId"]}, http_status=201)


def update_post(u, post_id: int, payload: dict):
    title = payload.get("title")
    content = payload.get("content")
    file_url = payload.get("fileUrl")

    p = db.get_post(post_id, increase_hits=False)
    if not p:
        raise_http_error(404, "NOT_FOUND")
    if p["authorUserId"] != u["userId"]:
        raise_http_error(403, "FORBIDDEN")

    if not title:
        raise_http_error(400, "TITLE_REQUIRED")
    if len(title) > 26:
        raise_http_error(400, "TITLE_TOO_LONG")
    if not content:
        raise_http_error(400, "CONTENT_REQUIRED")

    real_file_url = None
    if file_url and file_url.startswith("data:"):
        fid = db.save_file(file_url)
        if fid:
            real_file_url = f"/public/files/{fid}"
    else:
        real_file_url = file_url

    db.update_post(post_id, title, content, real_file_url)
    return success_response("POST_UPDATED", None)


def delete_post(u, post_id: int):
    p = db.get_post(post_id, increase_hits=False)
    if not p:
        raise_http_error(404, "NOT_FOUND")
    if p["authorUserId"] != u["userId"]:
        raise_http_error(403, "FORBIDDEN")

    db.delete_post(post_id)
    return success_response("POST_DELETED", None)


def like_post(u, post_id: int):
    if not db.get_post(post_id, increase_hits=False):
        raise_http_error(404, "NOT_FOUND")
    cnt = db.like_post(post_id, u["userId"])
    return success_response("POST_LIKED", {"likeCount": cnt}, http_status=201)


def unlike_post(u, post_id: int):
    if not db.get_post(post_id, increase_hits=False):
        raise_http_error(404, "NOT_FOUND")
    cnt = db.unlike_post(post_id, u["userId"])
    return success_response("POST_UNLIKED", {"likeCount": cnt})


def list_comments(post_id: int):
    if not db.get_post(post_id, increase_hits=False):
        raise_http_error(404, "NOT_FOUND")
    items = db.list_comments(post_id)
    return success_response("COMMENTS_RETRIEVED", {"items": items})


def create_comment(u, post_id: int, payload: dict):
    content = payload.get("content")
    if not content:
        raise_http_error(400, "COMMENT_REQUIRED")
    if not db.get_post(post_id, increase_hits=False):
        raise_http_error(404, "NOT_FOUND")

    c = db.create_comment(post_id, content, u["userId"])
    return success_response("COMMENT_CREATED", {"commentId": c["commentId"]}, http_status=201)


def update_comment(u, post_id: int, comment_id: int, payload: dict):
    content = payload.get("content")
    if not content:
        raise_http_error(400, "COMMENT_REQUIRED")

    c = db.get_comment(comment_id)
    if not c or c["postId"] != post_id:
        raise_http_error(404, "NOT_FOUND")
    if c["authorUserId"] != u["userId"]:
        raise_http_error(403, "FORBIDDEN")

    db.update_comment(comment_id, content)
    return success_response("COMMENT_UPDATED", None)


def delete_comment(u, post_id: int, comment_id: int):
    c = db.get_comment(comment_id)
    if not c or c["postId"] != post_id:
        raise_http_error(404, "NOT_FOUND")
    if c["authorUserId"] != u["userId"]:
        raise_http_error(403, "FORBIDDEN")

    db.delete_comment(comment_id)
    return success_response("COMMENT_DELETED", None)
