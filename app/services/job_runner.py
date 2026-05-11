import asyncio
import logging

from app.models.db import AsyncSessionLocal, Job, JobStatus, Quiz, Transcript
from app.services.preprocessor import remove_noise
from app.services.quiz_generator import generate_quizzes
from app.services.stt.base import STTBase

logger = logging.getLogger(__name__)


async def run_pipeline(job_id: int, audio_path: str, stt: STTBase) -> None:
    """WAV 청크 하나에 대한 STT → 노이즈 제거 → 퀴즈 생성 → DB 저장 파이프라인."""
    logger.info("job_id=%d pipeline 시작: %s", job_id, audio_path)

    # ── 1. 상태 → processing ────────────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        job = await db.get(Job, job_id)
        if job is None:
            logger.error("job_id=%d DB에서 찾을 수 없음 — pipeline 중단", job_id)
            return
        job.status = JobStatus.processing
        await db.commit()

    # ── 2. STT / 전처리 / 퀴즈 생성 ────────────────────────────────────────
    try:
        # STT는 blocking CPU/GPU 작업 → thread pool에서 실행
        segments: list[dict] = await asyncio.to_thread(stt.transcribe, audio_path)
        logger.info("job_id=%d STT 완료: %d 세그먼트", job_id, len(segments))

        clean_segments = remove_noise(segments)

        full_text = " ".join(s["text"].strip() for s in clean_segments)

        # LLM 호출도 blocking HTTP → thread pool에서 실행
        quizzes: list[dict] = await asyncio.to_thread(generate_quizzes, full_text)

    except Exception as exc:
        logger.error("job_id=%d pipeline 실패: %s", job_id, exc, exc_info=True)
        async with AsyncSessionLocal() as db:
            job = await db.get(Job, job_id)
            if job:
                job.status = JobStatus.failed
                job.error_message = str(exc)
                await db.commit()
        raise

    # ── 3. DB 저장 + 상태 → done ────────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        db.add(Transcript(job_id=job_id, full_text=full_text, segments=clean_segments))
        db.add(Quiz(job_id=job_id, quizzes=quizzes))
        job = await db.get(Job, job_id)
        job.status = JobStatus.done
        await db.commit()

    logger.info("job_id=%d pipeline 완료: 퀴즈 %d개", job_id, len(quizzes))
