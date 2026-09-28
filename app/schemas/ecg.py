from pydantic import BaseModel


class ECGUploadResponse(BaseModel):
    ecg_id: str
    status: str
    original_filename: str