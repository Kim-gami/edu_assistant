import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, DateTime, Enum, ForeignKey, JSON, String, Text, func,
)
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings


# ── 엔진 & 세션 ───────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    echo=(settings.app_env == "development"),
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """앱 시작 시 엔진 연결 확인용. 테이블 생성은 Alembic이 담당."""
    async with engine.connect() as conn:
        await conn.close()


async def get_session() -> AsyncSession:
    """FastAPI Depends에서 사용하는 DB 세션 의존성."""
    async with AsyncSessionLocal() as session:
        yield session


# ── Base ─────────────────────────────────────────────────────────────────────

class Base(AsyncAttrs, DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class JobStatus(str, enum.Enum):
    pending    = "pending"
    processing = "processing"
    done       = "done"
    failed     = "failed"


class QuizType(str, enum.Enum):
    multiple_choice = "multiple_choice"
    true_false      = "true_false"
    short_answer    = "short_answer"


class Difficulty(str, enum.Enum):
    easy   = "easy"
    medium = "medium"
    hard   = "hard"


# ── 테이블 모델 ───────────────────────────────────────────────────────────────

class Job(Base):
    """오디오 업로드 → 퀴즈 생성까지 하나의 작업 단위."""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    audio_filename: Mapped[str] = mapped_column(String(255))
    audio_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.pending
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    transcript: Mapped["Transcript | None"] = relationship(back_populates="job", uselist=False)
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="job")


class Transcript(Base):
    """STT 전사 결과. 원문 전체 + 청크 단위 타임스탬프."""
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), unique=True)
    full_text: Mapped[str] = mapped_column(Text)
    # [{"start": 0.0, "end": 3.2, "text": "..."}, ...] 형태로 저장
    segments: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["Job"] = relationship(back_populates="transcript")


class Quiz(Base):
    """LLM이 생성한 퀴즈 세트. CLAUDE.md의 JSON 스키마를 그대로 저장."""
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"))
    # quizzes 배열 전체를 JSON으로 저장 (CLAUDE.md 스키마 참고)
    quizzes: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped["Job"] = relationship(back_populates="quizzes")
