# ADR-002: LLM 모델 선택

## 상태: 확정 (2026-05-11)

## 결정
**Qwen2.5-7B-Instruct** (로컬 서빙: Ollama)

## 이유
- 7B 파라미터로 소비자 GPU(8GB VRAM)에서 실행 가능
- 한국어 지원 양호
- Ollama의 OpenAI-compatible API 사용 → 나중에 GPT-4o-mini 등으로 교체 시 코드 변경 없음
- 비용 없음 (로컬 추론)

## 서빙 방식
- Ollama (`http://localhost:11434/v1`)
- `openai` Python SDK로 호출 (base_url만 변경하면 클라우드 LLM으로 전환 가능)

## 설정
| 항목 | 값 |
|------|----|
| 모델 | qwen2.5:7b-instruct |
| temperature | 0.3 (일관된 JSON 출력) |
| max_tokens | 2048 |
| response_format | json_object |

## 준비 사항
```bash
# Ollama 설치 후
ollama pull qwen2.5:7b-instruct
```
