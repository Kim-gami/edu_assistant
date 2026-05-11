import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.models.db import init_db
from app.routers import capture, upload, quiz, status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시: DB 엔진 초기화 (테이블 생성은 Alembic이 담당)
    logger.info("Starting up — initializing DB engine")
    await init_db()
    yield
    # 종료 시: 진행 중인 캡처 정리 후 종료
    from app.services.audio.session import get_session
    session = get_session()
    if session is not None:
        logger.info("Shutting down — 진행 중인 캡처 강제 중지")
        session.capture.stop()
        session.buffer.stop()
    logger.info("Shutting down")


app = FastAPI(
    title="Lecture Quiz Generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(capture.router, prefix="/api/v1", tags=["capture"])
app.include_router(upload.router,  prefix="/api/v1", tags=["upload"])
app.include_router(quiz.router,    prefix="/api/v1", tags=["quiz"])
app.include_router(status.router,  prefix="/api/v1", tags=["status"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
