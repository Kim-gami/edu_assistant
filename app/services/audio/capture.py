import logging
import threading

import pyaudiowpatch as pyaudio

from app.services.audio.base import AudioChunkCallback, CaptureBase

logger = logging.getLogger(__name__)

FRAMES_PER_BUFFER = 512  # 한 번에 읽는 프레임 수. 작을수록 지연 감소, 클수록 CPU 부담 감소


class WASAPICapture(CaptureBase):
    """Windows WASAPI loopback을 통해 시스템 재생 오디오를 캡처한다.

    마이크가 아닌 스피커 출력을 직접 녹음하므로 강의 영상, 화상회의 등에 사용 가능.
    """

    def __init__(self) -> None:
        self._pa: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._sample_rate: int | None = None
        self._channels: int | None = None

    # ── CaptureBase 구현 ────────────────────────────────────────────────────

    def start(self, on_chunk: AudioChunkCallback) -> None:
        if self._running:
            raise RuntimeError("이미 캡처 중입니다")

        self._pa = pyaudio.PyAudio()
        device_info = self._get_loopback_device()

        self._sample_rate = int(device_info["defaultSampleRate"])
        self._channels = device_info["maxInputChannels"]

        logger.info(
            "WASAPI loopback 시작: device=%s rate=%d ch=%d",
            device_info["name"],
            self._sample_rate,
            self._channels,
        )

        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self._channels,
            rate=self._sample_rate,
            frames_per_buffer=FRAMES_PER_BUFFER,
            input=True,
            input_device_index=device_info["index"],
        )

        self._running = True
        self._thread = threading.Thread(
            target=self._read_loop,
            args=(on_chunk,),
            daemon=True,
            name="wasapi-capture",
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa:
            self._pa.terminate()
        self._stream = None
        self._pa = None
        logger.info("WASAPI loopback 중지")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def sample_rate(self) -> int | None:
        return self._sample_rate

    @property
    def channels(self) -> int | None:
        return self._channels

    # ── 내부 구현 ───────────────────────────────────────────────────────────

    def _get_loopback_device(self) -> dict:
        """기본 출력 장치의 WASAPI loopback 장치 정보를 반환한다."""
        wasapi_info = self._pa.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_out_idx = wasapi_info["defaultOutputDevice"]
        device_info = self._pa.get_device_info_by_index(default_out_idx)

        # loopback 장치는 출력 장치와 동일한 index를 input으로 사용
        if not device_info.get("isLoopbackDevice", False):
            # pyaudiowpatch는 loopback 장치를 별도로 열거함
            for i in range(self._pa.get_device_count()):
                d = self._pa.get_device_info_by_index(i)
                if d.get("isLoopbackDevice") and d["name"].startswith(device_info["name"]):
                    return d
            raise RuntimeError(
                f"WASAPI loopback 장치를 찾을 수 없습니다 (기본 출력: {device_info['name']})"
            )
        return device_info

    def _read_loop(self, on_chunk: AudioChunkCallback) -> None:
        """백그라운드 스레드에서 스트림을 읽고 on_chunk를 호출한다."""
        assert self._stream is not None
        assert self._sample_rate is not None
        assert self._channels is not None

        while self._running:
            try:
                raw = self._stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                on_chunk(raw, self._sample_rate, self._channels)
            except Exception as exc:
                logger.error("캡처 스트림 읽기 오류: %s", exc, exc_info=True)
                self._running = False
                break
