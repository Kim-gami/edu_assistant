import logging

from app.services.stt.base import STTBase
from app.services.preprocessor import remove_noise
from app.services.quiz_generator import generate_quizzes

logger = logging.getLogger(__name__)


async def run_pipeline(job_id: int, audio_path: str, stt: STTBase) -> None:
    """오디오 → STT → 노이즈 제거 → 퀴즈 생성 → DB 저장 파이프라인.

    STTBase를 주입받아 구현체와 독립적으로 동작한다.
    """
    # TODO(phase1): DB 세션 의존성 주입 방식으로 리팩터
    logger.info("job_id=%d pipeline start", job_id)

    # 1. STT
    segments = stt.transcribe(audio_path)
    logger.info("job_id=%d transcribed %d segments", job_id, len(segments))

    # 2. 노이즈 제거
    clean_segments = remove_noise(segments)

    # 3. 퀴즈 생성
    full_text = " ".join(s["text"].strip() for s in clean_segments)
    quizzes = generate_quizzes(full_text)

    # TODO(phase1): Transcript, Quiz DB 저장
    logger.info("job_id=%d pipeline done, quizzes=%d", job_id, len(quizzes))
