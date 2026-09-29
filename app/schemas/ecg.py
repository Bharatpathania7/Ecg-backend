from pydantic import BaseModel, Field


class WaveformResponse(BaseModel):
    format: str
    available: bool


class DigitalECGResponse(BaseModel):
    format: str
    available: bool


class ECGUploadResponse(BaseModel):
    ecg_id: str
    status: str
    original_filename: str

    layout: str | None = None
    matching_cost: float | None = None

    extracted_leads: list[str] = Field(
        default_factory=list
    )

    sample_count: int = 0

    waveform: WaveformResponse

    digital_ecg: DigitalECGResponse