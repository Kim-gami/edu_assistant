import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Job
from app.models.db import get_session as get_db_session
from app.models.schemas import JobStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> JobStatusResponse:
    job: Job | None = await db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"job_id={job_id} 를 찾을 수 없습니다")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error_message=job.error_message,
    )
