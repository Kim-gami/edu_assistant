# ADR-001: STT 모델 선택

## 상태: 확정 (2026-05-11)

## 비교 대상
- faster-whisper
- whisperx

## 결정
**faster-whisper** 채택

## 이유
- whisperx는 word-level 정렬을 제공하지만, 이 서비스는 세그먼트 단위 텍스트만 필요
- faster-whisper는 CTranslate2 기반으로 동일 모델 대비 속도가 빠르고 VRAM을 적게 사용
- 한국어 지원: Whisper large-v3 기준 충분한 정확도
- 의존성이 단순해 유지보수 용이
- vad_filter 내장으로 별도 전처리 없이 무음 구간 제거 가능

## 설정
| 항목 | 값 |
|------|----|
| 모델 | large-v3 |
| GPU | float16 |
| CPU | int8 |
| 언어 | ko (고정) |
| beam_size | 5 |
| VAD | 활성화 (min_silence=500ms) |
