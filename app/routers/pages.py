import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Job, JobStatus, Quiz
from app.models.db import get_session as get_db_session
from app.services.audio.session import get_session as get_capture_session

logger = logging.getLogger(__name__)
router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    capture = get_capture_session()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_job_id": capture.job_id if capture else None,
    })


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_page(request: Request, job_id: int) -> HTMLResponse:
    return templates.TemplateResponse("job.html", {
        "request": request,
        "job_id": job_id,
    })


@router.get("/fragments/status/{job_id}", response_class=HTMLResponse)
async def status_fragment(
    request: Request,
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> HTMLResponse:
    job: Job | None = await db.get(Job, job_id)
    quiz = None
    if job and job.status == JobStatus.done:
        result = await db.execute(
            select(Quiz)
            .where(Quiz.job_id == job_id)
            .order_by(Quiz.created_at.desc())
            .limit(1)
        )
        quiz = result.scalar_one_or_none()

    return templates.TemplateResponse("fragments/status.html", {
        "request": request,
        "job": job,
        "quiz": quiz,
    })
