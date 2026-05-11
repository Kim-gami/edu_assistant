# CLAUDE.md — Lecture Quiz Generator

## 프로젝트 개요

강의 오디오를 캡처해 자동으로 퀴즈를 생성하는 서비스.
소규모 팀/스터디 그룹이 강의 복습용으로 사용하는 것을 목표로 한다.

**오디오 입력 방식**: 브라우저의 `getDisplayMedia` API로 시스템 오디오를 캡처 후
WebSocket으로 서버에 스트리밍한다. Chrome/Edge 전용.

> **전환 배경**: 초기에는 Windows WASAPI loopback(pyaudiowpatch)으로 구현했으나,
> Windows 전용 하드웨어 API 특성상 Docker 컨테이너(Linux)에서 실행이 불가능했다.
> 풀 컨테이너화를 위해 브라우저 캡처(getDisplayMedia + WebSocket) 방식으로 전환했다.

---

## 기술 스택 및 결정 원칙

### 확정된 스택
- **언어**: Python 3.13
- **API 서버**: FastAPI
- **DB**: PostgreSQL (SQLAlchemy ORM + asyncpg)
- **컨테이너**: Docker + Docker Compose (풀 컨테이너화 완료)
- **오케스트레이션**: Kubernetes (최종 단계)
- **배포**: AWS (Phase 3, EC2 단일 서버 → EKS 전환)
- **오디오 캡처**: 브라우저 `getDisplayMedia` + WebSocket 스트리밍
  - Float32 PCM → Int16 변환 후 WebSocket 이진 전송
  - 서버에서 16000Hz mono 30초 WAV 청크로 버퍼링
  - Chrome / Edge 전용 (Firefox 미지원)

### 확정된 모델
- **STT**: `faster-whisper==1.1.1` (ADR-001)
  - 모델: large-v3, VAD 내장, 한국어 고정
  - GPU: float16 / CPU: int8 (`config.py` `STT_DEVICE`, `STT_COMPUTE_TYPE`으로 제어)
- **LLM**: `Qwen2.5-7B-Instruct` via Ollama (ADR-002)
  - Ollama 로컬/컨테이너 서빙, OpenAI-compatible API
  - `openai` SDK 사용 → `base_url`만 바꾸면 클라우드 LLM으로 전환 가능
- **임베딩 모델**: 노이즈 제거용, 한국어 지원 모델 우선 검토 (Phase 2)

---

## 아키텍처

```
브라우저 (Chrome/Edge)
    getDisplayMedia → Int16 PCM → WebSocket /ws/audio
    ↓
FastAPI (Docker)
    WebSocket 수신 → 30초 WAV 청크 버퍼링
    ↓
STT (faster-whisper, Docker)
    ↓
텍스트 전처리 — 임베딩 기반 top-k 노이즈/메타 제거
    ↓
PostgreSQL (Docker)
    ↓
LLM 퀴즈 생성 — Ollama (Docker)
    ↓
FastAPI 서빙 → 브라우저 웹 UI
    ↓
Docker Compose → AWS EC2 → Kubernetes
```

### Docker Compose 서비스 구성
```
services:
  db       — postgres:15-alpine (5432)
  ollama   — ollama/ollama (11434), ~/.ollama 볼륨 마운트
  app      — edu_assistant-app (8000), HuggingFace 캐시 볼륨 마운트
```

### 비동기 처리 원칙
WebSocket 수신 → `ChunkBuffer` (30초) → WAV → `run_pipeline` (asyncio.to_thread)
→ STT → 노이즈 제거 → LLM → DB 저장

---

## 디렉토리 구조

```
lecture-quiz/
├── CLAUDE.md
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh             # alembic upgrade head → uvicorn 시작
├── requirements.txt
├── alembic/                  # DB 마이그레이션
├── app/
│   ├── main.py
│   ├── config.py             # 환경변수 관리 (pydantic-settings)
│   ├── routers/
│   │   ├── ws_audio.py       # WebSocket /ws/audio — 브라우저 오디오 수신
│   │   ├── upload.py         # POST /upload (파일 직접 업로드 — 선택적)
│   │   ├── quiz.py           # GET /quiz/{id}
│   │   ├── status.py         # GET /status/{job_id}
│   │   └── pages.py          # 웹 UI 페이지 라우터
│   ├── services/
│   │   ├── audio/
│   │   │   └── buffer.py     # 청크 단위 버퍼링 + WAV 저장
│   │   ├── stt/
│   │   │   ├── base.py       # STT 추상 인터페이스
│   │   │   └── faster_whisper_impl.py
│   │   ├── preprocessor.py   # 임베딩 기반 노이즈 제거 (현재 pass-through)
│   │   ├── quiz_generator.py # LLM 퀴즈 생성
│   │   └── job_runner.py     # 백그라운드 파이프라인
│   ├── models/
│   │   ├── db.py             # SQLAlchemy 모델
│   │   └── schemas.py        # Pydantic 스키마
│   └── templates/            # Jinja2 웹 UI (HTMX + Tailwind)
├── tests/
└── scripts/
    └── benchmark_stt.py
```

---

## 코딩 컨벤션

### 일반 원칙
- 함수/클래스는 단일 책임. 100줄 넘으면 분리 검토
- 타입 힌트 필수. `Any` 사용 최소화
- 환경변수는 `config.py`에서 `pydantic-settings`로 관리. 코드에 하드코딩 금지
- 에러는 삼키지 말고 로깅 후 상위로 전파

### STT 인터페이스 (교체 가능성 유지)
```python
# services/stt/base.py — 반드시 이 인터페이스를 따를 것
from abc import ABC, abstractmethod

class STTBase(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> list[dict]:
        """
        Returns:
            [{"start": float, "end": float, "text": str}, ...]
        """
        pass
```

### 퀴즈 생성 JSON 스키마 (LLM 출력 강제)
```json
{
  "quizzes": [
    {
      "question": "질문 (개념 이해를 묻는 형태)",
      "type": "multiple_choice | true_false | short_answer",
      "difficulty": "easy | medium | hard",
      "choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "A",
      "explanation": "정답 이유와 오답이 왜 틀렸는지 포함"
    }
  ]
}
```

### DB 관련
- 마이그레이션은 반드시 Alembic으로 관리. 직접 DDL 실행 금지
- 쿼리는 SQLAlchemy ORM 우선. 복잡한 쿼리만 raw SQL 허용
- `alembic upgrade head`는 `entrypoint.sh`에서 컨테이너 시작 시 자동 실행됨
- migration 파일에서 `op.execute(sa.text(...))` 를 각 문장별로 분리 호출할 것
  (asyncpg는 단일 execute에 다중 SQL 불가)

---

## 기능 요구사항 (구현 우선순위 순)

### Phase 1 — MVP ✅ 완료
- [x] 브라우저 오디오 캡처 (getDisplayMedia + WebSocket)
- [x] faster-whisper 전사
- [x] 임베딩 기반 노이즈 제거 (현재 pass-through)
- [x] PostgreSQL 적재 (transcript + chunk 단위)
- [x] LLM 4지선다 퀴즈 생성
- [x] 퀴즈 웹 UI (문제 풀기 + 정답 확인)
- [x] Docker Compose 풀 컨테이너화 (app + db + ollama)

### Phase 2 — 품질 개선
- [ ] 문제 형식 선택 (4지선다 / 참거짓 / 단답형)
- [ ] 난이도 선택 (쉬움 / 보통 / 어려움)
- [ ] 오답 품질 개선 — 개념적으로 유사하지만 틀린 선택지 생성
- [ ] `preprocessor.py` 임베딩 기반 노이즈 제거 실구현
- [ ] 문제가 강의의 핵심 개념을 묻도록 프롬프트 튜닝
- [ ] 퀴즈 결과 공유 URL 생성
- [ ] 웹 UI React 전환 검토

### Phase 3 — 서비스화
- [ ] AWS EC2 단일 서버 배포
  - ECR에 이미지 push → EC2에서 docker compose up
  - RDS(PostgreSQL 관리형) 분리 검토
  - 인스턴스: 최소 16GB RAM (Qwen2.5-7B 구동), GPU 고려 시 g4dn.xlarge
- [ ] Kubernetes 전환 (EKS, `kompose convert`로 매니페스트 생성)
- [ ] LLM 모델 비교 후 최종 선정 (필요시 파인튜닝)

---

## 실험 및 비교 기록

`docs/decisions/` 에 ADR(Architecture Decision Record) 저장.
- ADR-001: STT 모델 선택 → faster-whisper 확정
- ADR-002: LLM 모델 선택 → Qwen2.5-7B-Instruct via Ollama 확정

---

## 현재 작업 상태

> 이 섹션은 세션마다 업데이트한다.

- **현재 Phase**: Phase 1 완료, Phase 2 준비 중 (2026-05-11)
- **마지막 완료 작업**:
  - **오디오 캡처 전환**: WASAPI(Windows 전용) → 브라우저 getDisplayMedia + WebSocket
    - `app/routers/ws_audio.py` 신규 구현
    - `app/templates/index.html` 브라우저 캡처 UI로 교체
    - pyaudiowpatch 의존성 제거
  - **풀 컨테이너화**:
    - `Dockerfile`: python:3.13-slim, ffmpeg/libgomp1 설치, entrypoint.sh 실행
    - `entrypoint.sh`: alembic upgrade head → uvicorn 자동 실행
    - `docker-compose.yml`: app + db + ollama 3서비스 구성
    - HuggingFace 캐시(`~/.cache/huggingface`) 볼륨 마운트 (재다운로드 방지)
    - Ollama 모델(`~/.ollama`) 볼륨 마운트 (재다운로드 방지)
  - **기타 수정**:
    - `requirements.txt`: greenlet 추가, pyaudiowpatch 제거, faster-whisper 1.1.1
    - `alembic.ini`: 한글 주석 제거 (Windows cp949 인코딩 충돌 수정)
    - `alembic/versions/0001_initial.py`: op.execute(sa.text(...)) 방식으로 재작성
  - **E2E 파이프라인 동작 확인**: 브라우저 캡처 → STT → 퀴즈 생성 → 웹 UI 렌더링

- **다음 작업**:
  1. Docker 컨테이너 전체 스택 기동 테스트 (`docker compose up`)
  2. Phase 2 기능 개발 시작
     - 우선순위: `preprocessor.py` 노이즈 제거 실구현 (임베딩 모델 선정 필요)
     - 문제 형식 / 난이도 파라미터 UI 노출

- **블로커**: 없음

---

## 알려진 미결 사항

- `preprocessor.py` 노이즈 제거 미구현 (현재 pass-through) — Phase 2
- 웹 UI React 전환 검토 예정 — Phase 2
- AWS 배포 시 EC2 인스턴스 타입 미확정 (비용/성능 트레이드오프)
- Ollama GPU 가속: Docker에서 NVIDIA GPU 사용 시 `deploy.resources.reservations.devices` 설정 필요
