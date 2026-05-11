import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Quiz
from app.models.db import get_session as get_db_session
from app.models.schemas import QuizResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/quiz/job/{job_id}", response_model=QuizResponse)
async def get_quiz_by_job(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> QuizResponse:
    """캡처 완료 후 job_id로 퀴즈 조회. 가장 최근 생성된 퀴즈를 반환."""
    result = await db.execute(
        select(Quiz)
        .where(Quiz.job_id == job_id)
        .order_by(Quiz.created_at.desc())
        .limit(1)
    )
    quiz: Quiz | None = result.scalar_one_or_none()
    if quiz is None:
        raise HTTPException(
            status_code=404,
            detail=f"job_id={job_id} 에 대한 퀴즈가 없습니다. 아직 생성 중이거나 실패했을 수 있습니다.",
        )

    return QuizResponse(
        quiz_id=quiz.id,
        job_id=quiz.job_id,
        quizzes=quiz.quizzes,
        created_at=quiz.created_at,
    )


@router.get("/quiz/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> QuizResponse:
    """quiz_id로 직접 조회."""
    quiz: Quiz | None = await db.get(Quiz, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail=f"quiz_id={quiz_id} 를 찾을 수 없습니다")

    return QuizResponse(
        quiz_id=quiz.id,
        job_id=quiz.job_id,
        quizzes=quiz.quizzes,
        created_at=quiz.created_at,
    )
