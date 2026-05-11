"""faster-whisper vs whisperx 벤치마크 스크립트.

사용법:
    python scripts/benchmark_stt.py --audio path/to/sample.wav --reference path/to/ref.txt

평가 항목:
    - WER (Word Error Rate): 전사 정확도. 낮을수록 좋다.
    - RTF (Real-Time Factor): 처리시간 / 오디오길이. 1.0 미만이면 실시간 이상.
    - Peak VRAM (MB): GPU 메모리 사용량.
"""
import argparse
import time

# TODO(phase1): 아래 라이브러리 requirements.txt에 추가 후 주석 해제
# import torch
# from jiwer import wer  # WER 계산


def measure_wer(hypothesis: str, reference: str) -> float:
    # TODO(phase1): jiwer 라이브러리로 WER 계산
    raise NotImplementedError


def measure_vram_mb() -> float:
    # TODO(phase1): torch.cuda.max_memory_allocated() 활용
    raise NotImplementedError


def benchmark(audio_path: str, reference_text: str) -> None:
    results = {}

    for name, impl_class, kwargs in [
        ("faster-whisper", "FasterWhisperSTT", {"model_size": "large-v3"}),
        ("whisperx",       "WhisperXSTT",      {"model_size": "large-v3"}),
    ]:
        # TODO(phase1): 구현체 import 후 실제 측정
        print(f"[{name}] 벤치마크 예정")

    # TODO(phase1): 결과를 docs/decisions/ADR-001.md 형식으로 출력


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio",     required=True, help="테스트 오디오 파일 경로")
    parser.add_argument("--reference", required=True, help="정답 전사 텍스트 파일 경로")
    args = parser.parse_args()

    with open(args.reference, encoding="utf-8") as f:
        ref = f.read()

    benchmark(args.audio, ref)
