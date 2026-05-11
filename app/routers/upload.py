from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import JobResponse

router = APIRouter()


@router.post("/upload", response_model=JobResponse, status_code=202)
async def upload_audio(file: UploadFile = File(...)) -> JobResponse:
    # TODO(phase1): 파일 저장 → Job 생성 → BackgroundTask로 파이프라인 실행
    allowed = {"audio/mpeg", "audio/wav", "audio/x-m4a", "audio/mp4"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail="mp3/wav/m4a만 허용")
    raise HTTPException(status_code=501, detail="Not implemented yet")
