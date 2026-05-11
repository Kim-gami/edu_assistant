# Claude Code 초기 세션 프롬프트

아래 텍스트를 Claude Code 첫 세션에 그대로 붙여넣어라.
프로젝트 루트에 CLAUDE.md가 있는 상태에서 실행할 것.

---

## 붙여넣을 프롬프트

```
CLAUDE.md를 읽고 프로젝트 전체 컨텍스트를 파악해라.

지금 이 세션의 목표는 Phase 1 MVP의 뼈대를 세팅하는 것이다.
아래 순서대로 진행해라. 각 단계 완료 후 내가 확인하면 다음으로 넘어가라.

## 이번 세션 작업 목록

1. 디렉토리 구조 생성
   - CLAUDE.md에 정의된 구조 그대로 생성
   - 각 __init__.py 포함

2. Docker Compose 세팅
   - 서비스: app(FastAPI), db(PostgreSQL 15), 필요시 redis
   - .env.example 파일 포함 (실제 .env는 생성하지 말 것)
   - PostgreSQL는 처음 사용하므로 docker-compose.yml 주요 설정 주석 설명 포함

3. FastAPI 앱 뼈대
   - main.py: 라우터 등록, lifespan으로 DB 연결 초기화
   - config.py: pydantic-settings 기반 환경변수 관리
   - 헬스체크 엔드포인트: GET /health

4. SQLAlchemy + Alembic 초기 세팅
   - 비동기 엔진 (asyncpg)
   - Job, Transcript, Quiz 테이블 모델 초안
   - Alembic 초기화 및 첫 마이그레이션 파일 생성
   - PostgreSQL 처음이므로 alembic upgrade head 실행 방법도 설명

5. STT 추상 인터페이스
   - services/stt/base.py: CLAUDE.md의 STTBase 인터페이스 구현
   - faster_whisper_impl.py, whisperx_impl.py 스텁 생성
   - scripts/benchmark_stt.py 스캐폴딩 (벤치마크 로직은 나중에)

## 작업 원칙
- 파일 생성 전 "지금 X를 만들겠다" 한 줄 알려라
- 코드에 TODO 남길 때는 // TODO(phase): 이유 형식으로
- PostgreSQL, Alembic처럼 내가 처음 쓰는 기술은 핵심 개념 2-3줄 설명 후 코드 작성
- 막히거나 결정이 필요한 부분은 임의로 결정하지 말고 나한테 물어봐라
```

---

## 이후 세션 시작 프롬프트 템플릿

매 세션 시작할 때 아래 형식으로 시작해라:

```
CLAUDE.md를 읽어라.

지난 세션 요약:
- 완료: [무엇을 했는지]
- 현재 상태: [코드/파일 상태]
- 이번 목표: [오늘 할 것]

이번 세션에서 [구체적인 작업] 을 구현할 것이다.
시작 전에 현재 파일 구조를 확인하고 CLAUDE.md의 구조와 맞는지 체크해라.
```

---

## 특정 작업별 프롬프트 스니펫

### STT 벤치마크 실행 시
```
scripts/benchmark_stt.py를 구현해라.
테스트 오디오는 [경로] 를 사용한다.
측정 항목: WER, RTF(Real Time Factor), 최대 VRAM 사용량, 한국어 전사 샘플.
결과를 docs/decisions/ADR-001-stt-model.md 형식으로 출력해라.
CLAUDE.md의 ADR 형식을 따를 것.
```

### 퀴즈 생성 프롬프트 튜닝 시
```
현재 퀴즈 품질 문제:
- [구체적인 문제 예시]

quiz_generator.py의 프롬프트를 개선해라.
요구사항:
1. 오답은 강의 내 다른 개념을 활용해서 헷갈리게 만들 것
2. 질문은 단순 암기가 아닌 개념 이해를 물을 것
3. 난이도 파라미터(easy/medium/hard)가 실질적으로 반영될 것
개선 전/후 프롬프트를 나란히 보여주고 왜 바꿨는지 설명해라.
```

### PostgreSQL 스키마 변경 시
```
[테이블/컬럼] 을 변경해야 한다.
1. SQLAlchemy 모델 수정
2. Alembic 마이그레이션 파일 생성 (alembic revision --autogenerate)
3. 마이그레이션 파일 내용 확인 후 실행 방법 알려줘
직접 DDL 실행하지 말고 반드시 Alembic으로 관리할 것.
```

### Docker 빌드/배포 시
```
현재 Docker Compose 로컬 환경을 [클라우드 제공사] 배포용으로 전환해라.
- Dockerfile 프로덕션 최적화 (멀티스테이지 빌드)
- 환경변수 시크릿 관리 방법
- 헬스체크 설정
Kubernetes 전환을 고려해서 설정을 분리해둘 것.
```
