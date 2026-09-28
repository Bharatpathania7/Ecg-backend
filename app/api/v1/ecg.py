from fastapi import APIRouter, File, UploadFile

from app.schemas.ecg import ECGUploadResponse
from app.services.ecg_service import ECGService


router = APIRouter(
    prefix="/ecg",
    tags=["ECG"],
)


@router.post(
    "",
    response_model=ECGUploadResponse,
)
async def upload_ecg(
    file: UploadFile = File(...),
):
    return await ECGService.upload_ecg(file)