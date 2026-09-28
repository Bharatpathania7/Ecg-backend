import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


class StorageService:

    @staticmethod
    def generate_ecg_id() -> str:
        return f"ecg_{uuid.uuid4().hex}"

    @staticmethod
    async def save_original(
        file: UploadFile,
        ecg_id: str,
        content: bytes,
    ) -> Path:

        extension = Path(file.filename or "").suffix.lower()

        file_path = settings.ORIGINALS_DIR / f"{ecg_id}{extension}"

        # Write only to our generated path.
        # Never use the user's filename as the storage filename.
        file_path.write_bytes(content)

        return file_path