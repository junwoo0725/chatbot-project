from datetime import datetime, timedelta
from typing import Optional, List
import uuid
import base64
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.orm import User, Session as DBSession, Post, Comment, File, Conversation, Message

# Initialize tables (Creating tables if not exist)
Base.metadata.create_all(bind=engine)

def now_kst():
    return datetime.utcnow() + timedelta(hours=9)

def now_iso() -> str:
    return now_kst().isoformat()

def new_id() -> str:
    return str(uuid.uuid4())

# Helper to get DB session
def get_db_session():
    return SessionLocal()

# ---------- Helper: Convert ORM to Dict ----------
def to_user_dict(u: User) -> dict:
    if not u:
        return None
    return {
        "userId": u.id,
        "email": u.email,
        "passwordHash": u.password_hash,
        "nickname": u.nickname,
        "profileImageUrl": u.profile_image_url,
        "createdAt": u.created_at.isoformat(), # Simple formatting
        "updatedAt": u.updated_at.isoformat(),
    }

def to_post_dict(p: Post, user_id_for_like: Optional[int] = None) -> dict:
    if not p:
        return None
    
    # Calculate likes count
    like_count = len(p.likers)
    
    return {
        "postId": p.id,
        "title": p.title,
        "content": p.content,
        "authorUserId": p.author_user_id,
        "fileUrl": p.file_url,
        "hits": p.hits,
        "likeCount": like_count,
        "createdAt": p.created_at.isoformat(),
        "updatedAt": p.updated_at.isoformat(),
    }

def to_comment_dict(c: Comment) -> dict:
    if not c:
        return None
    return {
        "commentId": c.id,
        "postId": c.post_id,
        "authorUserId": c.author_user_id,
        "content": c.content,
        "createdAt": c.created_at.isoformat(),
        "updatedAt": c.updated_at.isoformat(),
    }


# ---------- User functions ----------
def create_user(email: str, pw_hash: str, nickname: str, profile_url: Optional[str]):
    db = get_db_session()
    try:
        user = User(
            email=email,
            password_hash=pw_hash,
            nickname=nickname,
            profile_image_url=profile_url
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return to_user_dict(user)
    finally:
        db.close()

def get_user(user_id: int) -> Optional[dict]:
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        return to_user_dict(user)
    finally:
        db.close()

def get_user_by_email(email: str) -> Optional[dict]:
    db = get_db_session()
    try:
        user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
        return to_user_dict(user)
    finally:
        db.close()

def get_user_by_nickname(nickname: str) -> Optional[dict]:
    db = get_db_session()
    try:
        user = db.query(User).filter(User.nickname == nickname, User.deleted_at.is_(None)).first()
        return to_user_dict(user)
    finally:
        db.close()

def update_user_nickname(user_id: int, nickname: str):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.nickname = nickname
            user.updated_at = now_kst()
            db.commit()
    finally:
        db.close()

def update_user_password(user_id: int, password_hash: str):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.password_hash = password_hash
            user.updated_at = now_kst()
            db.commit()
    finally:
        db.close()

def update_user_profile_image(user_id: int, profile_url: str):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.profile_image_url = profile_url
            user.updated_at = now_kst()
            db.commit()
    finally:
        db.close()

def delete_user(user_id: int):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Soft Delete: Set deleted_at AND change unique fields (email, nickname)
            # to allow re-signup with the same email/nickname.
            ts = int(now_kst().timestamp())
            user.deleted_at = now_kst()
            user.email = f"del_{ts}_{user.email}"
            # Nickname max 50 chars. Ensure uniqueness but fit in length.
            user.nickname = f"del_{ts}_{user.nickname}"[:50]
            
            # Delete all sessions for this user so they are logged out everywhere
            db.query(DBSession).filter(DBSession.user_id == user_id).delete()
            
            # Cascade Soft Delete: Posts
            db.query(Post).filter(Post.author_user_id == user_id).update({Post.deleted_at: now_kst()}, synchronize_session=False)

            # Cascade Soft Delete: Comments
            db.query(Comment).filter(Comment.author_user_id == user_id).update({Comment.deleted_at: now_kst()}, synchronize_session=False)
            
            db.commit()
    finally:
        db.close()

# ---------- Session functions ----------
def create_session(user_id: int) -> str:
    db = get_db_session()
    try:
        sid = new_id()
        session = DBSession(session_id=sid, user_id=user_id)
        db.add(session)
        db.commit()
        return sid
    finally:
        db.close()

def delete_session(session_id: str):
    db = get_db_session()
    try:
        session = db.query(DBSession).filter(DBSession.session_id == session_id).first()
        if session:
            db.delete(session)
            db.commit()
    finally:
        db.close()

def session_user(session_id: str) -> Optional[dict]:
    db = get_db_session()
    try:
        session = db.query(DBSession).filter(DBSession.session_id == session_id).first()
        # Ensure user exists AND is not deleted
        if session and session.user and not session.user.deleted_at:
            return to_user_dict(session.user)
        return None
    finally:
        db.close()

# ---------- Post functions ----------
def create_post(title: str, content: str, author_user_id: int, file_url: Optional[str]):
    db = get_db_session()
    try:
        post = Post(
            title=title,
            content=content,
            author_user_id=author_user_id,
            file_url=file_url
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return to_post_dict(post)
    finally:
        db.close()

def update_post(post_id: int, title: str, content: str, file_url: Optional[str]):
    db = get_db_session()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.title = title
            post.content = content
            post.file_url = file_url
            db.commit()
    finally:
        db.close()

def delete_post(post_id: int):
    db = get_db_session()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.deleted_at = now_kst()
            db.commit()
    finally:
        db.close()

def get_post(post_id: int, increase_hits: bool = True) -> Optional[dict]:
    db = get_db_session()
    try:
        post = db.query(Post).join(User, Post.author_user_id == User.id)\
            .filter(Post.id == post_id, Post.deleted_at.is_(None), User.deleted_at.is_(None)).first()
        if not post:
            return None
        
        if increase_hits:
            post.hits += 1
            db.commit()
            db.refresh(post)
            
        return to_post_dict(post)
    finally:
        db.close()

def list_posts(offset: int, limit: int) -> List[dict]:
    db = get_db_session()
    try:
        posts = db.query(Post).join(User, Post.author_user_id == User.id)\
            .filter(Post.deleted_at.is_(None), User.deleted_at.is_(None))\
            .order_by(Post.created_at.desc()).offset(offset).limit(limit).all()
        return [to_post_dict(p) for p in posts]
    finally:
        db.close()

def like_post(post_id: int, user_id: int) -> int:
    db = get_db_session()
    try:
        post = db.query(Post).filter(Post.id == post_id, Post.deleted_at.is_(None)).first()
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        
        if post and user:
            if user not in post.likers:
                post.likers.append(user)
                db.commit()
                db.refresh(post)
        return len(post.likers) if post else 0
    finally:
        db.close()

def unlike_post(post_id: int, user_id: int) -> int:
    db = get_db_session()
    try:
        post = db.query(Post).filter(Post.id == post_id, Post.deleted_at.is_(None)).first()
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        
        if post and user:
            if user in post.likers:
                post.likers.remove(user)
                db.commit()
                db.refresh(post)
        return len(post.likers) if post else 0
    finally:
        db.close()


# ---------- Comment functions ----------
def create_comment(post_id: int, content: str, author_user_id: int) -> dict:
    db = get_db_session()
    try:
        comment = Comment(
            post_id=post_id,
            content=content,
            author_user_id=author_user_id
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return to_comment_dict(comment)
    finally:
        db.close()

def get_comment(comment_id: int) -> Optional[dict]:
    db = get_db_session()
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at.is_(None)).first()
        return to_comment_dict(comment)
    finally:
        db.close()

def update_comment(comment_id: int, content: str):
    db = get_db_session()
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.deleted_at.is_(None)).first()
        if comment:
            comment.content = content
            db.commit()
    finally:
        db.close()

def delete_comment(comment_id: int):
    db = get_db_session()
    try:
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if comment:
            comment.deleted_at = now_kst()
            db.commit()
    finally:
        db.close()

def list_comments(post_id: int) -> List[dict]:
    db = get_db_session()
    try:
        comments = db.query(Comment).join(User, Comment.author_user_id == User.id)\
            .filter(Comment.post_id == post_id, Comment.deleted_at.is_(None), User.deleted_at.is_(None))\
            .order_by(Comment.created_at.asc()).all()
        return [to_comment_dict(c) for c in comments]
    finally:
        db.close()

# ---------- File functions ----------
def save_file(base64_str: str) -> str:
    # 1. Split header/data: "data:image/png;base64,....."
    if "," in base64_str:
        header, data_str = base64_str.split(",", 1)
        # Extract mime
        # header e.g. "data:image/png;base64"
        mime = header.split(":", 1)[1].split(";", 1)[0]
    else:
        # Fallback
        data_str = base64_str
        mime = "application/octet-stream"

    # 2. Decode
    binary_data = base64.b64decode(data_str)

    # 3. Save to DB
    fid = new_id()
    db = get_db_session()
    try:
        f = File(id=fid, mime_type=mime, data=binary_data)
        db.add(f)
        db.commit()
        return fid
    finally:
        db.close()

def get_file_data(file_id: str):
    db = get_db_session()
    try:
        f = db.query(File).filter(File.id == file_id).first()
        if f:
            return f.data, f.mime_type
        return None, None
    finally:
        db.close()

# ---------- Chat functions ----------
def get_conversations(user_id: int) -> List[dict]:
    db = get_db_session()
    try:
        convs = db.query(Conversation).filter(
            (Conversation.user1_id == user_id) | (Conversation.user2_id == user_id)
        ).all()
        
        result = []
        for c in convs:
            other_user = c.user2 if c.user1_id == user_id else c.user1
            if not other_user or other_user.deleted_at:
                continue
                
            last_message = None
            last_message_at = c.updated_at
            unread_count = 0
            
            if c.messages:
                last_msg = c.messages[-1]
                last_message = last_msg.content
                last_message_at = last_msg.created_at
                
                # Count unread
                for m in c.messages:
                    if m.sender_id != user_id and not m.is_read:
                        unread_count += 1
                        
            result.append({
                "id": c.id,
                "other_user_id": other_user.id,
                "other_user_nickname": other_user.nickname,
                "other_user_profile": other_user.profile_image_url,
                "last_message": last_message,
                "last_message_at": last_message_at,
                "unread_count": unread_count
            })
            
        # Sort by last_message_at desc safely
        def safe_date(d):
            if isinstance(d, datetime): return d
            if isinstance(d, str):
                try: return datetime.fromisoformat(str(d).replace('Z', '+00:00'))
                except ValueError: return datetime.min
            return datetime.min
            
        result.sort(key=lambda x: safe_date(x["last_message_at"]), reverse=True)
        return result
    finally:
        db.close()

def get_or_create_conversation(user1_id: int, user2_id: int) -> int:
    # Ensure user1_id < user2_id for consistency
    u1, u2 = min(user1_id, user2_id), max(user1_id, user2_id)
    db = get_db_session()
    try:
        conv = db.query(Conversation).filter(
            Conversation.user1_id == u1,
            Conversation.user2_id == u2
        ).first()
        
        if not conv:
            conv = Conversation(user1_id=u1, user2_id=u2)
            db.add(conv)
            db.commit()
            db.refresh(conv)
            
        return conv.id
    finally:
        db.close()

def get_messages(conversation_id: int, limit: int = 50) -> List[dict]:
    db = get_db_session()
    try:
        messages = db.query(Message).filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at.desc()).limit(limit).all()
            
        result = []
        for m in reversed(messages): # reverse to make it chronological
            result.append({
                "id": m.id,
                "conversation_id": m.conversation_id,
                "sender_id": m.sender_id,
                "content": m.content,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat()
            })
        return result
    finally:
        db.close()

def create_message(conversation_id: int, sender_id: int, content: str) -> dict:
    db = get_db_session()
    try:
        msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content
        )
        db.add(msg)
        
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.updated_at = now_kst()
            
        db.commit()
        db.refresh(msg)
        
        return {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "sender_id": msg.sender_id,
            "content": msg.content,
            "is_read": msg.is_read,
            "created_at": msg.created_at.isoformat()
        }
    finally:
        db.close()

def mark_messages_read(conversation_id: int, target_user_id: int):
    # mark messages sent *to* target_user_id as read
    db = get_db_session()
    try:
        db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender_id != target_user_id,
            Message.is_read == False
        ).update({"is_read": True})
        db.commit()
    finally:
        db.close()

