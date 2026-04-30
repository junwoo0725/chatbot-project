import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers.index import register_routers
from app.utils.responses import success_response
from app.utils.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────
    # Import here to avoid circular imports at module load time
    from app.controllers.chat_controller import manager
    task = asyncio.create_task(manager.subscribe_loop())

    yield

    # ── Shutdown ─────────────────────────────────────
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await close_redis()


app = FastAPI(title="Community API", lifespan=lifespan)

# ✅ 쿠키 기반 세션이면 "*" 절대 금지
FRONT_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:80",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://3.35.126.220",
    "http://3.35.126.220:80",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONT_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={"code": "BAD_REQUEST", "message": "Bad request"},
    )


@app.get("/health")
def health():
    return success_response("OK", None)


register_routers(app)

# ✅ AWS Lambda용 핸들러 (Mangum) 추가
handler = Mangum(app)
