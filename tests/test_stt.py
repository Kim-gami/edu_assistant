import pytest
from app.services.stt.base import STTBase


class DummySTT(STTBase):
    def transcribe(self, audio_path: str) -> list[dict]:
        return [{"start": 0.0, "end": 1.0, "text": "안녕하세요"}]


def test_transcribe_to_text():
    stt = DummySTT()
    assert stt.transcribe_to_text("dummy.wav") == "안녕하세요"


def test_transcribe_returns_segments():
    stt = DummySTT()
    result = stt.transcribe("dummy.wav")
    assert isinstance(result, list)
    assert all({"start", "end", "text"} <= seg.keys() for seg in result)
