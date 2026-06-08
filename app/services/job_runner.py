import asyncio
import logging

from app.models.db import AsyncSessionLocal, Job, JobStatus, Quiz, Transcript
from app.services.preprocessor import remove_noise
from app.services.quiz_generator import generate_quizzes
from app.services.stt.base import STTBase

logger = logging.getLogger(__name__)


async def run_pipeline_chunk(
    job_id: int,
    audio_path: str,
    stt: STTBase,
    all_segments: list[dict],
) -> None:
    """WAV 청크 하나를 STT 처리해 결과를 all_segments에 누적한다. 퀴즈는 생성하지 않는다."""
    logger.info("job_id=%d chunk STT 시작: %s", job_id, audio_path)

    async with AsyncSessionLocal() as db:
        job = await db.get(Job, job_id)
        if job is None:
            logger.error("job_id=%d DB에서 찾을 수 없음 — chunk 중단", job_id)
            return
        if job.status == JobStatus.pending:
            job.status = JobStatus.processing
            await db.commit()

    try:
        segments: list[dict] = await asyncio.to_thread(stt.transcribe, audio_path)
        logger.info("job_id=%d chunk STT 완료: %d 세그먼트", job_id, len(segments))
        all_segments.extend(segments)
    except Exception as exc:
        logger.error("job_id=%d chunk STT 실패: %s", job_id, exc, exc_info=True)
        raise


async def finalize_job(job_id: int, all_segments: list[dict]) -> None:
    """누적된 전체 세그먼트로 노이즈 제거 → 퀴즈 생성 → DB 저장을 수행한다."""
    logger.info("job_id=%d finalize 시작: 총 %d 세그먼트", job_id, len(all_segments))

    if not all_segments:
        logger.warning("job_id=%d 세그먼트 없음 — 퀴즈 생성 건너뜀", job_id)
        async with AsyncSessionLocal() as db:
            job = await db.get(Job, job_id)
            if job:
                job.status = JobStatus.failed
                job.error_message = "전사된 텍스트가 없습니다"
                await db.commit()
        return

    try:
        clean_segments = remove_noise(all_segments)
        full_text = " ".join(s["text"].strip() for s in clean_segments)

        # LLM 호출은 blocking HTTP → thread pool에서 실행
        quizzes: list[dict] = await asyncio.to_thread(generate_quizzes, full_text)

    except Exception as exc:
        logger.error("job_id=%d finalize 실패: %s", job_id, exc, exc_info=True)
        async with AsyncSessionLocal() as db:
            job = await db.get(Job, job_id)
            if job:
                job.status = JobStatus.failed
                job.error_message = str(exc)
                await db.commit()
        raise

    async with AsyncSessionLocal() as db:
        db.add(Transcript(job_id=job_id, full_text=full_text, segments=clean_segments))
        db.add(Quiz(job_id=job_id, quizzes=quizzes))
        job = await db.get(Job, job_id)
        job.status = JobStatus.done
        await db.commit()

    logger.info("job_id=%d finalize 완료: 퀴즈 %d개", job_id, len(quizzes))
