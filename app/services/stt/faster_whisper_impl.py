from app.services.stt.base import STTBase


class FasterWhisperSTT(STTBase):
    def __init__(self, model_size: str = "large-v3", device: str = "cuda", compute_type: str = "float16"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        # TODO(phase1): from faster_whisper import WhisperModel 후 모델 로드
        self._model = None

    def transcribe(self, audio_path: str) -> list[dict]:
        # TODO(phase1): faster-whisper 실제 전사 구현
        # segments, info = self._model.transcribe(audio_path, language="ko")
        # return [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
        raise NotImplementedError("faster-whisper 구현 예정 — 벤치마크 후 확정")
