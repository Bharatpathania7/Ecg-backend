from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "ECG Digitization API"
    APP_VERSION: str = "1.0.0"

    STORAGE_DIR: Path = BASE_DIR / "storage"
    ORIGINALS_DIR: Path = STORAGE_DIR / "originals"
    PROCESSED_DIR: Path = STORAGE_DIR / "processed"
    SIGNALS_DIR: Path = STORAGE_DIR / "signals"
    METADATA_DIR: Path = STORAGE_DIR / "metadata"

    # Upload security
    MAX_UPLOAD_SIZE_MB: int = 10

    ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png"}

    ALLOWED_CONTENT_TYPES: set[str] = {
        "image/jpeg",
        "image/png",
    }

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()