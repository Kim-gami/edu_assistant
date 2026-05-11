import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.models.db import init_db
from app.routers import capture, upload, quiz, status, pages

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
        logger.warning("faster-whisper 미설치 — STT 비활성화. pip install faster-whisper==1.1.4")
        app.state.stt = None

    yield

    session = get_session()
    if session is not None:
        logger.info("Shutting down — 진행 중인 캡처 강제 중지")
        session.capture.stop()
        session.buffer.stop()
    logger.info("Shutting down")


from app.services.audio.session import get_session  # noqa: E402 — lifespan 내부에서 사용

app = FastAPI(
    title="Lecture Quiz Generator",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(pages.router)   # 웹 UI — prefix 없음 (/, /jobs/{id}, /fragments/*)
app.include_router(capture.router, prefix="/api/v1", tags=["capture"])
app.include_router(upload.router,  prefix="/api/v1", tags=["upload"])
app.include_router(quiz.router,    prefix="/api/v1", tags=["quiz"])
app.include_router(status.router,  prefix="/api/v1", tags=["status"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
