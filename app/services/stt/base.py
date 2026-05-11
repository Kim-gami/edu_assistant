from abc import ABC, abstractmethod


class STTBase(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> list[dict]:
        """오디오 파일을 전사해 타임스탬프 세그먼트 목록을 반환한다.

        Returns:
            [{"start": float, "end": float, "text": str}, ...]
        """
        ...

    def transcribe_to_text(self, audio_path: str) -> str:
        """전체 전사 텍스트만 필요할 때 사용하는 편의 메서드."""
        segments = self.transcribe(audio_path)
        return " ".join(seg["text"].strip() for seg in segments)
