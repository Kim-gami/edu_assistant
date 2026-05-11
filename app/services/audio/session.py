"""캡처 세션 상태 관리.

Phase 1: 단일 프로세스 모듈 레벨 상태로 관리.
Phase 2: Redis 등 외부 상태 저장소로 전환 예정.
"""
import asyncio
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path

from app.services.audio.base import CaptureBase
from app.services.audio.buffer import ChunkBuffer
from app.services.stt.base import STTBase

logger = logging.getLogger(__name__)


@dataclass
class CaptureSession:
    job_id: int
    capture: CaptureBase
    buffer: ChunkBuffer
    stt: STTBase
    loop: asyncio.AbstractEventLoop = field(repr=False)
    wav_paths: list[Path] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def on_wav_ready(self, path: Path) -> None:
        """ChunkBuffer가 WAV 청크를 저장할 때마다 호출되는 콜백.

        buffer._flush()는 백그라운드 스레드에서 실행되므로,
        asyncio 코루틴인 run_pipeline을 메인 이벤트 루프에 안전하게 스케줄한다.
        """
        with self._lock:
            self.wav_paths.append(path)

        from app.services.job_runner import run_pipeline

        future = asyncio.run_coroutine_threadsafe(
            run_pipeline(self.job_id, str(path), self.stt),
            self.loop,
        )
        future.add_done_callback(
            lambda f: logger.error("job_id=%d pipeline 예외: %s", self.job_id, f.exception())
            if f.exception()
            else None
        )


_current_session: CaptureSession | None = None
_session_lock = threading.Lock()


def get_session() -> CaptureSession | None:
    return _current_session


def set_session(session: CaptureSession | None) -> None:
    global _current_session
    with _session_lock:
        _current_session = session
