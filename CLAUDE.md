# CLAUDE.md — Lecture Quiz Generator

## 프로젝트 개요

강의 오디오를 캡처해 자동으로 퀴즈를 생성하는 서비스.
소규모 팀/스터디 그룹이 강의 복습용으로 사용하는 것을 목표로 한다.

**오디오 입력 방식**: 파일 업로드가 아닌 시스템 오디오 실시간 캡처.
Windows WASAPI loopback을 통해 컴퓨터에서 재생되는 소리(강의 영상, 화상회의 등)를
직접 캡처한다. 개발 환경 및 타깃 플랫폼은 Windows 고정.

---

## 기술 스택 및 결정 원칙

### 확정된 스택
- **언어**: Python 3.11+
- **API 서버**: FastAPI
- **DB**: PostgreSQL (SQLAlchemy ORM + asyncpg)
- **컨테이너**: Docker + Docker Compose
- **오케스트레이션**: Kubernetes (최종 단계)
- **배포**: 클라우드 (GCP / AWS / Azure 중 미확정)
- **시스템 오디오 캡처**: `pyaudiowpatch` (Windows WASAPI loopback)
  - 마이크가 아닌 컴퓨터 재생 오디오를 직접 캡처
  - 캡처 → 버퍼링 → WAV 청크 저장 → STT 파이프라인으로 전달
  - **Windows 전용**: 다른 OS 지원 계획 없음

### 미확정 — 실험 후 결정
- **STT 모델**: `faster-whisper` 확정 (2026-05-11, ADR-001 참고)
  - 모델: large-v3, VAD 내장, 한국어 고정
  - GPU: float16 / CPU: int8 (config.py `STT_DEVICE`, `STT_COMPUTE_TYPE`으로 제어)
- **LLM**: `Qwen2.5-7B-Instruct` 확정 (2026-05-11, ADR-002 참고)
  - Ollama 로컬 서빙, OpenAI-compatible API (`http://localhost:11434/v1`)
  - `openai` SDK 사용 → base_url만 바꾸면 클라우드 LLM으로 전환 가능
- **임베딩 모델**: 노이즈 제거용, 한국어 지원 모델 우선 검토

---

## 아키텍처

```
시스템 오디오 캡처 (pyaudiowpatch / WASAPI loopback)
    ↓ WAV 청크 (30초 단위 버퍼링)
STT (faster-whisper or whisperx)
    ↓
텍스트 전처리 — 임베딩 기반 top-k 노이즈/메타 제거
    ↓
PostgreSQL 적재 (transcript + chunk 단위)
    ↓
LLM 퀴즈 생성 (형식·난이도 파라미터 포함)
    ↓
FastAPI 서빙
    ↓
Docker → 클라우드 배포 → Kubernetes
```

### 비동기 처리 원칙
오디오 전사 + LLM 생성은 HTTP 요청 사이클 밖에서 처리한다.
`FastAPI BackgroundTasks` → 작업량 증가시 Celery + Redis로 전환.
클라이언트는 `GET /status/{job_id}` 폴링으로 완료 확인.

---

## 디렉토리 구조

```
lecture-quiz/
├── CLAUDE.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── alembic/                  # DB 마이그레이션
├── app/
│   ├── main.py
│   ├── config.py             # 환경변수 관리 (pydantic-settings)
│   ├── routers/
│   │   ├── capture.py        # POST /capture/start, /capture/stop
│   │   ├── upload.py         # POST /upload (파일 직접 업로드 — 선택적)
│   │   ├── quiz.py           # GET /quiz/{id}
│   │   └── status.py         # GET /status/{job_id}
│   ├── services/
│   │   ├── audio/
│   │   │   ├── capture.py    # WASAPI loopback 캡처 (pyaudiowpatch)
│   │   │   └── buffer.py     # 청크 단위 버퍼링 + WAV 저장
│   │   ├── stt/
│   │   │   ├── base.py       # STT 추상 인터페이스
│   │   │   ├── whisperx_impl.py
│   │   │   └── faster_whisper_impl.py
│   │   ├── preprocessor.py   # 임베딩 기반 노이즈 제거
│   │   ├── quiz_generator.py # LLM 퀴즈 생성
│   │   └── job_runner.py     # 백그라운드 파이프라인
│   ├── models/
│   │   ├── db.py             # SQLAlchemy 모델
│   │   └── schemas.py        # Pydantic 스키마
│   └── templates/            # Jinja2 웹 UI
├── tests/
│   ├── test_stt.py
│   ├── test_preprocessor.py
│   └── test_quiz_generator.py
└── scripts/
    └── benchmark_stt.py      # faster-whisper vs whisperx 벤치마크
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
구현체가 바뀌어도 `job_runner.py`는 수정하지 않는 것이 목표.

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
- PostgreSQL 처음 사용하므로 스키마 변경 시 마이그레이션 파일 생성 방법도 함께 설명

---

## 기능 요구사항 (구현 우선순위 순)

### Phase 1 — MVP
- [ ] **시스템 오디오 캡처** (pyaudiowpatch / Windows WASAPI loopback)
  - 캡처 시작/중지: `POST /capture/start`, `POST /capture/stop`
  - 30초 단위 WAV 청크 버퍼링 후 STT 파이프라인으로 전달
- [ ] WhisperX 또는 faster-whisper 전사
- [ ] 임베딩 기반 노이즈 제거 (인트로/아웃트로/잡담 필터링)
- [ ] PostgreSQL 적재 (transcript 원문 + 청크)
- [ ] LLM 4지선다 퀴즈 생성
- [ ] 퀴즈 웹 UI (문제 풀기 + 정답 확인)
- [ ] Docker Compose로 로컬 실행

### Phase 2 — 품질 개선
- [ ] 문제 형식 선택 (4지선다 / 참거짓 / 단답형)
- [ ] 난이도 선택 (쉬움 / 보통 / 어려움)
- [ ] 오답 품질 개선 — 개념적으로 유사하지만 틀린 선택지 생성
  - 전략: 같은 강의 내 다른 개념 활용 또는 LLM에 "혼동하기 쉬운 오답" 명시 지시
- [ ] 문제가 강의의 핵심 개념을 묻도록 프롬프트 튜닝
- [ ] 퀴즈 결과 공유 URL 생성

### Phase 3 — 서비스화
- [ ] STT 모델 벤치마크 후 최종 선정
- [ ] LLM 모델 비교 후 최종 선정 (필요시 파인튜닝)
- [ ] 클라우드 배포 (단일 서버)
- [ ] Kubernetes 전환

---

## 실험 및 비교 기록

각 기술 선택 시 아래 형식으로 `docs/decisions/` 에 ADR(Architecture Decision Record) 저장.

```markdown
# ADR-001: STT 모델 선택

## 상태: 결정 전 / 실험 중 / 확정

## 비교 대상
- faster-whisper
- whisperx

## 평가 기준 및 결과
| 항목 | faster-whisper | whisperx |
|------|----------------|----------|
| WER (한국어) | - | - |
| RTF | - | - |
| VRAM | - | - |

## 결정
...

## 이유
...
```

---

## 현재 작업 상태

> 이 섹션은 세션마다 업데이트한다.

- **현재 Phase**: Phase 1 MVP 완성 (2026-05-11)
- **마지막 완료 작업**:
  - **STT 확정**: `faster-whisper==1.1.4` (ADR-001), `faster_whisper_impl.py` 실구현, `whisperx_impl.py` 삭제
  - **LLM 확정**: `Qwen2.5-7B-Instruct` via Ollama (ADR-002), `quiz_generator.py` 실구현
  - **`config.py`**: STT/LLM 설정값 추가 (`stt_*`, `llm_*`)
  - **API 라우터**: `status.py` (`GET /status/{job_id}`), `quiz.py` (`GET /quiz/{quiz_id}`, `GET /quiz/job/{job_id}`)
  - **파이프라인 연결**:
    - `job_runner.py`: STT → 노이즈 제거 → 퀴즈 생성 → DB 저장, Job 상태 `pending→processing→done/failed`. blocking 작업 `asyncio.to_thread` 처리. DB 세션 3분리
    - `session.py`: `stt`/`loop` 필드 추가, `on_wav_ready`에서 `asyncio.run_coroutine_threadsafe`로 메인 루프에 파이프라인 스케줄
    - `capture.py`: `Request`로 `app.state.stt`/`app.state.loop` 주입, STT 미설치 시 503
    - `main.py`: 앱 시작 시 STT 모델 로드(`asyncio.to_thread`), `app.state.loop` 저장
  - **웹 UI** (HTMX + Tailwind CSS):
    - `routers/pages.py`: `GET /`, `GET /jobs/{job_id}`, `GET /fragments/status/{job_id}`
    - `templates/index.html`: 캡처 시작/중지
    - `templates/job.html`: HTMX 폴링 컨테이너
    - `templates/fragments/status.html`: pending/processing(3초 폴링) → done(퀴즈 렌더링+채점) / failed(에러) 자동 전환
  - `requirements.txt`: `pyaudiowpatch 0.2.12.8`, `asyncpg 0.31.0`, `faster-whisper==1.1.4`, `openai==1.56.0` 확정
  - `.env` 생성, 기본 패키지 `py -m pip install` 완료

- **다음 작업**:
  1. Docker Desktop 설치 (`winget install Docker.DockerDesktop`)
  2. `docker compose up -d`
  3. `py -m alembic upgrade head`
  4. `py -m pip install faster-whisper==1.1.4 openai==1.56.0`
  5. Ollama 설치 → `ollama pull qwen2.5:7b-instruct`
  6. `py -m uvicorn app.main:app --reload`
  7. 브라우저 `http://localhost:8000` → 캡처 → 퀴즈 엔드투엔드 확인

- **블로커**: Docker Desktop 미설치

---

## 알려진 미결 사항

- `preprocessor.py` 노이즈 제거 미구현 (현재 pass-through) — 임베딩 모델 미확정 (Phase 2)
- 웹 UI React 전환 예정 (Phase 2, 현재 HTMX+Tailwind로 운영)
- 클라우드 제공사 미확정 (Phase 3)
