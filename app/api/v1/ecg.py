import json
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.ecg import ECGUploadResponse
from app.services.ecg_service import ECGService


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/ecg",
    tags=["ECG"],
)


# --------------------------------
# Upload ECG
# --------------------------------

@router.post(
    "",
    response_model=ECGUploadResponse,
)
async def upload_ecg(
    file: UploadFile = File(...),
):
    try:
        return await ECGService.upload_ecg(file)

    except HTTPException:
        raise

    except RuntimeError as exc:
        logger.warning(
            "ECG processing request failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected ECG API error."
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error.",
        ) from exc


# --------------------------------
# Get ECG processing status
# --------------------------------

@router.get(
    "/{ecg_id}/status",
)
async def get_ecg_status(
    ecg_id: str,
):
    status_path = (
        settings.METADATA_DIR
        / ecg_id
        / "status.json"
    )

    if not status_path.exists():
        raise HTTPException(
            status_code=404,
            detail="ECG not found.",
        )

    try:
        status_data = json.loads(
            status_path.read_text(
                encoding="utf-8"
            )
        )

    except (OSError, json.JSONDecodeError) as exc:
        logger.exception(
            "Failed to read ECG status: %s",
            ecg_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to read ECG status.",
        ) from exc

    return status_data


# --------------------------------
# Get waveform CSV
# --------------------------------

@router.get(
    "/{ecg_id}/waveform",
)
async def get_waveform(
    ecg_id: str,
):
    waveform_path = (
        settings.SIGNALS_DIR
        / ecg_id
        / f"{ecg_id}_timeseries_canonical.csv"
    )

    if not waveform_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Waveform not found.",
        )

    return FileResponse(
        path=waveform_path,
        media_type="text/csv",
        filename=f"{ecg_id}.csv",
    )


# --------------------------------
# Get digital ECG image
# --------------------------------

@router.get(
    "/{ecg_id}/digital",
)
async def get_digital_ecg(
    ecg_id: str,
):
    digital_ecg_path = (
        settings.SIGNALS_DIR
        / ecg_id
        / f"{ecg_id}.png"
    )

    if not digital_ecg_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Digital ECG image not found.",
        )

    return FileResponse(
        path=digital_ecg_path,
        media_type="image/png",
        filename=f"{ecg_id}_digital.png",
    )