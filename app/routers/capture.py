import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import CaptureStartResponse, CaptureStopResponse
from app.services.audio.buffer import ChunkBuffer
from app.services.audio.capture import WASAPICapture
from app.services.audio.session import CaptureSession, get_session, set_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/capture/start", response_model=CaptureStartResponse, status_code=202)
async def start_capture() -> CaptureStartResponse:
    if get_session() is not None:
        raise HTTPException(status_code=409, detail="이미 캡처가 진행 중입니다")

    # TODO(phase1): DB에 Job 레코드 생성 후 job_id 발급
    job_id: int = 1  # 임시 고정값 — DB 연동 후 교체

    capture = WASAPICapture()

    session = CaptureSession(job_id=job_id, capture=capture, buffer=None)  # type: ignore[arg-type]
    buffer = ChunkBuffer(
        output_dir=settings.upload_dir,
        chunk_duration_sec=30,
        on_wav_ready=session.on_wav_ready,
    )
    session.buffer = buffer
    set_session(session)

    try:
        capture.start(on_chunk=buffer.feed)
    except Exception as exc:
        set_session(None)
        logger.error("캡처 시작 실패: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"캡처 장치 오류: {exc}") from exc

    logger.info("캡처 시작 — job_id=%d", job_id)
    return CaptureStartResponse(job_id=job_id, message="캡처를 시작했습니다")


@router.post("/capture/stop", response_model=CaptureStopResponse)
async def stop_capture() -> CaptureStopResponse:
    session = get_session()
    if session is None:
        raise HTTPException(status_code=409, detail="현재 진행 중인 캡처가 없습니다")

    session.capture.stop()
    session.buffer.stop()   # 남은 버퍼 플러시
    set_session(None)

    wav_count = len(session.wav_paths)
    logger.info("캡처 중지 — job_id=%d wav_chunks=%d", session.job_id, wav_count)

    return CaptureStopResponse(
        job_id=session.job_id,
        wav_chunks_saved=wav_count,
        message=f"캡처를 중지했습니다. WAV 청크 {wav_count}개 저장됨",
    )
