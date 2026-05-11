from fastapi import APIRouter, HTTPException
from app.models.schemas import QuizResponse

router = APIRouter()


@router.get("/quiz/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: int) -> QuizResponse:
    # TODO(phase1): DB에서 quiz_id에 해당하는 퀴즈 조회
    raise HTTPException(status_code=501, detail="Not implemented yet")
