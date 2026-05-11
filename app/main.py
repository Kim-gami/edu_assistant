import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.models.db import init_db
from app.routers import upload, quiz, status, pages, ws_audio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initializing DB engine")
    await init_db()

    app.state.loop = asyncio.get_running_loop()

    try:
        from app.services.stt.faster_whisper_impl import FasterWhisperSTT
        logger.info("STT 모델 로드 중 (faster-whisper)...")
        app.state.stt = await asyncio.to_thread(FasterWhisperSTT)
        logger.info("STT 모델 로드 완료")
    except ImportError:
        logger.warning("faster-whisper 미설치 — STT 비활성화")
        app.state.stt = None

    yield

    logger.info("Shutting down")


app = FastAPI(
    title="Lecture Quiz Generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(pages.router)
app.include_router(ws_audio.router)
app.include_router(upload.router,  prefix="/api/v1", tags=["upload"])
app.include_router(quiz.router,    prefix="/api/v1", tags=["quiz"])
app.include_router(status.router,  prefix="/api/v1", tags=["status"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
