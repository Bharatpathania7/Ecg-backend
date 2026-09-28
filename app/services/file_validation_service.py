from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


class FileValidationService:

    @staticmethod
    async def validate(file: UploadFile) -> bytes:
        """
        Validate an uploaded ECG image.

        Checks:
        1. Filename exists
        2. Extension is allowed
        3. MIME type is allowed
        4. File size is within limit
        5. File is actually a valid image
        """

        # 1. Filename validation
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required.",
            )

        # 2. Extension validation
        extension = Path(file.filename).suffix.lower()

        if extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type. Only JPEG and PNG images are allowed.",
            )

        # 3. MIME type validation
        if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Invalid content type. Only JPEG and PNG images are allowed.",
            )

        # 4. Read file
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=(
                    f"File is too large. Maximum allowed size is "
                    f"{settings.MAX_UPLOAD_SIZE_MB} MB."
                ),
            )

        # 5. Verify actual image
        try:
            with Image.open(file.file) as image:
                image.verify()

        except (UnidentifiedImageError, OSError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is not a valid image.",
            )

        # Reset pointer for future use
        await file.seek(0)

        return content