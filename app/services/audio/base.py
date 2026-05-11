from abc import ABC, abstractmethod
from typing import Callable

# raw PCM bytes, sample_rate(Hz), channels
AudioChunkCallback = Callable[[bytes, int, int], None]


class CaptureBase(ABC):
    """오디오 캡처 추상 인터페이스.

    Phase 1: WASAPICapture (Windows 호스트 직접 실행)
    Phase 2: RemoteCaptureAgent (capture_agent.py → FastAPI Docker 구조로 전환 시)
    """

    @abstractmethod
    def start(self, on_chunk: AudioChunkCallback) -> None:
        """캡처 시작. on_chunk(raw_bytes, sample_rate, channels)는 데이터가 쌓일 때마다 호출."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """캡처 중지 및 리소스 해제."""
        ...

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """현재 캡처 중인지 여부."""
        ...

    @property
    @abstractmethod
    def sample_rate(self) -> int | None:
        """캡처 중인 장치의 샘플레이트. 시작 전에는 None."""
        ...

    @property
    @abstractmethod
    def channels(self) -> int | None:
        """캡처 중인 장치의 채널 수. 시작 전에는 None."""
        ...
