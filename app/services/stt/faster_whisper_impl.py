import logging
from pathlib import Path

from faster_whisper import WhisperModel

from app.config import settings
from app.services.stt.base import STTBase

logger = logging.getLogger(__name__)


class FasterWhisperSTT(STTBase):
    """faster-whisper 기반 STT 구현체. GPU(float16) / CPU(int8) 모두 지원."""

    def __init__(
        self,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ) -> None:
        model_size = model_size or settings.stt_model_size
        device = device or settings.stt_device
        compute_type = compute_type or settings.stt_compute_type

        logger.info(
            "faster-whisper 모델 로드 중: model=%s device=%s compute_type=%s",
            model_size, device, compute_type,
        )
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("faster-whisper 모델 로드 완료")

    def transcribe(self, audio_path: str) -> list[dict]:
        logger.info("전사 시작: %s", Path(audio_path).name)

        segments, info = self._model.transcribe(
            audio_path,
            language="ko",
            beam_size=5,
            vad_filter=True,           # 무음 구간 자동 제거
            vad_parameters={"min_silence_duration_ms": 500},
        )

        result = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
        logger.info(
            "전사 완료: %d 세그먼트, 언어 확률=%.2f",
            len(result), info.language_probability,
        )
        return result
