from fastapi import UploadFile

from app.services.file_validation_service import FileValidationService
from app.services.storage_service import StorageService


class ECGService:

    @staticmethod
    async def upload_ecg(file: UploadFile):

        # Validate before generating/storing anything.
        content = await FileValidationService.validate(file)

        # Generate unique ID.
        ecg_id = StorageService.generate_ecg_id()

        # Save validated file.
        await StorageService.save_original(
            file=file,
            ecg_id=ecg_id,
            content=content,
        )

        return {
            "ecg_id": ecg_id,
            "status": "uploaded",
            "original_filename": file.filename,
        }