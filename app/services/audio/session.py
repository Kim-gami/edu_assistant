"""캡처 세션 상태 관리.

Phase 1: 단일 프로세스 모듈 레벨 상태로 관리.
Phase 2: Redis 등 외부 상태 저장소로 전환 예정.
"""
import threading
from dataclasses import dataclass, field
from pathlib import Path

from app.services.audio.base import CaptureBase
from app.services.audio.buffer import ChunkBuffer


@dataclass
class CaptureSession:
    job_id: int
    capture: CaptureBase
    buffer: ChunkBuffer
    wav_paths: list[Path] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def on_wav_ready(self, path: Path) -> None:
        with self._lock:
            self.wav_paths.append(path)
        # TODO(phase1): STT 파이프라인 트리거 (job_runner.run_pipeline 호출)


_current_session: CaptureSession | None = None
_session_lock = threading.Lock()


def get_session() -> CaptureSession | None:
    return _current_session


def set_session(session: CaptureSession | None) -> None:
    global _current_session
    with _session_lock:
        _current_session = session
