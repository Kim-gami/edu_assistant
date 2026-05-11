from app.services.stt.base import STTBase


class WhisperXSTT(STTBase):
    def __init__(self, model_size: str = "large-v3", device: str = "cuda", language: str = "ko"):
        self.model_size = model_size
        self.device = device
        self.language = language
        # TODO(phase1): import whisperx 후 모델 로드
        # whisperx는 faster-whisper 위에서 word-level 정렬을 추가로 제공
        self._model = None

    def transcribe(self, audio_path: str) -> list[dict]:
        # TODO(phase1): whisperx 실제 전사 구현
        # model = whisperx.load_model(self.model_size, self.device)
        # audio = whisperx.load_audio(audio_path)
        # result = model.transcribe(audio, language=self.language)
        # return [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in result["segments"]]
        raise NotImplementedError("whisperx 구현 예정 — 벤치마크 후 확정")
