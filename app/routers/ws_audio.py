import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.models.db import AsyncSessionLocal, Job, JobStatus
from app.services.audio.buffer import ChunkBuffer
from app.services.job_runner import run_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()

SAMPLE_RATE = 16000
CHANNELS = 1


@router.websocket("/ws/audio")
async def audio_websocket(websocket: WebSocket) -> None:
    await websocket.accept()

    stt = websocket.app.state.stt
    if stt is None:
        await websocket.send_json({"type": "error", "message": "STT 모델이 로드되지 않았습니다"})
        await websocket.close(code=1011)
        return

    async with AsyncSessionLocal() as db:
        job = Job(
            audio_filename="browser_capture",
            audio_path=str(settings.upload_dir),
            status=JobStatus.pending,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id: int = job.id

    await websocket.send_json({"type": "job_created", "job_id": job_id})
    logger.info("브라우저 캡처 시작 — job_id=%d", job_id)

    loop = asyncio.get_running_loop()

    def on_wav_ready(path: Path) -> None:
        future = asyncio.run_coroutine_threadsafe(
            run_pipeline(job_id, str(path), stt),
            loop,
        )
        future.add_done_callback(
            lambda f: logger.error("job_id=%d pipeline 예외: %s", job_id, f.exception())
            if f.exception()
            else None
        )

    buffer = ChunkBuffer(
        output_dir=settings.upload_dir,
        chunk_duration_sec=30,
        on_wav_ready=on_wav_ready,
    )

    try:
        async for data in websocket.iter_bytes():
            buffer.feed(data, SAMPLE_RATE, CHANNELS)
    except WebSocketDisconnect:
        logger.info("WebSocket 연결 종료 — job_id=%d", job_id)
    finally:
        buffer.stop()
        logger.info("버퍼 플러시 완료 — job_id=%d", job_id)
