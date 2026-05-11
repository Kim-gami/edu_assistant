from fastapi import APIRouter, HTTPException
from app.models.schemas import JobStatusResponse

router = APIRouter()


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: int) -> JobStatusResponse:
    # TODO(phase1): DB에서 job_id에 해당하는 작업 상태 조회
    raise HTTPException(status_code=501, detail="Not implemented yet")
