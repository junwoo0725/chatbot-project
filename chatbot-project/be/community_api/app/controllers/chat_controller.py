import json
import asyncio
from fastapi import WebSocket
from typing import Dict, List
from app.storage import db
from app.utils.responses import success_response, raise_http_error
from app.utils.redis_client import get_redis

# Redis channel prefix: chat:<conversation_id>
CHANNEL_PREFIX = "chat:"


class ConnectionManager:
    """
    Manages in-process WebSocket connections on THIS pod.
    Pub/Sub via Redis ensures messages are delivered even when
    sender and receiver are on different pods.
    """

    def __init__(self):
        # Maps user_id → list of WebSocket connections on THIS pod
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def publish_message(self, conversation_id: int, message: dict):
        """Publish message to Redis so ALL pods receive it."""
        redis = get_redis()
        channel = f"{CHANNEL_PREFIX}{conversation_id}"
        await redis.publish(channel, json.dumps(message))

    async def deliver_to_local(self, user_id: int, message: dict):
        """Send to WebSocket connections on THIS pod only."""
        if user_id in self.active_connections:
            dead = []
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws, user_id)

    async def subscribe_loop(self):
        """
        Background task: subscribe to all chat channels on Redis.
        When a message arrives, deliver it to local WebSocket connections.
        This runs once per pod on startup.
        """
        redis = get_redis()
        pubsub = redis.pubsub()
        # Subscribe to pattern chat:* to capture all conversation channels
        await pubsub.psubscribe(f"{CHANNEL_PREFIX}*")

        async for raw in pubsub.listen():
            if raw["type"] != "pmessage":
                continue
            try:
                msg = json.loads(raw["data"])
                conversation_id = msg.get("conversation_id")
                if conversation_id is None:
                    continue

                # Deliver to every user_id connected on THIS pod
                for user_id in list(self.active_connections.keys()):
                    await self.deliver_to_local(user_id, msg)
            except Exception:
                pass


manager = ConnectionManager()


# ──────────────────────────────────────────
# REST handlers
# ──────────────────────────────────────────

def get_my_conversations(u: dict):
    user_id = u["userId"]
    conversations = db.get_conversations(user_id)
    return success_response("CONVERSATIONS_RETRIEVED", conversations)


def get_conversation_messages(u: dict, conversation_id: int):
    convs = db.get_conversations(u["userId"])
    if not any(c["id"] == conversation_id for c in convs):
        raise_http_error(403, "FORBIDDEN")

    db.mark_messages_read(conversation_id, u["userId"])
    messages = db.get_messages(conversation_id)
    return success_response("MESSAGES_RETRIEVED", messages)


def create_or_get_conversation(u: dict, payload: dict):
    target_user_id = payload.get("other_user_id")
    if not target_user_id:
        raise_http_error(400, "OTHER_USER_ID_REQUIRED")

    if target_user_id == u["userId"]:
        raise_http_error(400, "CANNOT_CHAT_WITH_SELF")

    target_user = db.get_user(target_user_id)
    if not target_user:
        raise_http_error(404, "USER_NOT_FOUND")

    conv_id = db.get_or_create_conversation(u["userId"], target_user_id)
    return success_response("CONVERSATION_CREATED", {"conversation_id": conv_id})


# ──────────────────────────────────────────
# WebSocket handler
# ──────────────────────────────────────────

async def handle_chat_websocket(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            conversation_id = data.get("conversation_id")
            content = data.get("content")

            if not conversation_id or not content:
                continue

            # Verify user is part of this conversation
            convs = db.get_conversations(user_id)
            conv = next((c for c in convs if c["id"] == conversation_id), None)

            if not conv:
                await websocket.send_json({"error": "Forbidden"})
                continue

            # Save message to DB
            msg = db.create_message(conversation_id, user_id, content)

            # Publish to Redis → all pods (including this one) will deliver it
            await manager.publish_message(conversation_id, msg)

    except Exception:
        manager.disconnect(websocket, user_id)
