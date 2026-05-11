import io
import logging
import threading
import wave
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

WavReadyCallback = Callable[[Path], None]


class ChunkBuffer:
    """PCM 데이터를 축적해 지정된 시간(기본 30초) 단위로 WAV 파일을 생성한다.

    on_wav_ready(path)가 호출되면 STT 파이프라인이 해당 WAV를 처리한다.
    stop() 호출 시 남은 버퍼도 WAV로 플러시한다.
    """

    def __init__(
        self,
        output_dir: str | Path,
        chunk_duration_sec: int = 30,
        on_wav_ready: WavReadyCallback | None = None,
    ) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._chunk_duration_sec = chunk_duration_sec
        self._on_wav_ready = on_wav_ready

        self._lock = threading.Lock()
        self._frames: list[bytes] = []
        self._sample_rate: int | None = None
        self._channels: int | None = None
        self._accumulated_sec: float = 0.0
        self._chunk_index: int = 0

    def feed(self, raw_bytes: bytes, sample_rate: int, channels: int) -> None:
        """캡처에서 넘어온 PCM 청크를 버퍼에 추가하고, 임계값 도달 시 WAV로 저장한다."""
        with self._lock:
            if self._sample_rate is None:
                self._sample_rate = sample_rate
                self._channels = channels

            self._frames.append(raw_bytes)

            # 16-bit PCM: 샘플당 2바이트
            frames_count = len(raw_bytes) / (2 * channels)
            self._accumulated_sec += frames_count / sample_rate

            if self._accumulated_sec >= self._chunk_duration_sec:
                self._flush()

    def stop(self) -> None:
        """남은 버퍼를 플러시한다. 캡처 중지 시 호출."""
        with self._lock:
            if self._frames:
                logger.info("버퍼 플러시: %.1f초 남음", self._accumulated_sec)
                self._flush()

    def _flush(self) -> None:
        """현재 버퍼를 WAV 파일로 저장하고 on_wav_ready를 호출한다. _lock 보유 상태에서 호출."""
        if not self._frames or self._sample_rate is None:
            return

        wav_path = self._output_dir / f"chunk_{self._chunk_index:04d}.wav"
        self._write_wav(wav_path)

        logger.info("WAV 저장: %s (%.1f초)", wav_path.name, self._accumulated_sec)

        self._frames = []
        self._accumulated_sec = 0.0
        self._chunk_index += 1

        if self._on_wav_ready:
            # 콜백은 lock 밖에서 실행해야 교착 방지
            threading.Thread(
                target=self._on_wav_ready,
                args=(wav_path,),
                daemon=True,
                name=f"wav-ready-{self._chunk_index}",
            ).start()

    def _write_wav(self, path: Path) -> None:
        assert self._sample_rate is not None
        assert self._channels is not None

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(2)          # 16-bit = 2 bytes
            wf.setframerate(self._sample_rate)
            wf.writeframes(b"".join(self._frames))
