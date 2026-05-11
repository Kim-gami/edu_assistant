from datetime import datetime
from typing import Literal
from pydantic import BaseModel


# ── Job ───────────────────────────────────────────────────────────────────────

class JobResponse(BaseModel):
    job_id: int
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: int
    status: Literal["pending", "processing", "done", "failed"]
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


# ── Capture ──────────────────────────────────────────────────────────────────

class CaptureStartResponse(BaseModel):
    job_id: int
    message: str


class CaptureStopResponse(BaseModel):
    job_id: int
    wav_chunks_saved: int
    message: str


# ── Quiz ─────────────────────────────────────────────────────────────────────

class QuizItem(BaseModel):
    question: str
    type: Literal["multiple_choice", "true_false", "short_answer"]
    difficulty: Literal["easy", "medium", "hard"]
    choices: list[str]
    answer: str
    explanation: str


class QuizResponse(BaseModel):
    quiz_id: int
    job_id: int
    quizzes: list[QuizItem]
    created_at: datetime
