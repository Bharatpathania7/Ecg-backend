import json
import logging
import shutil
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.services.digitizer_service import DigitizerService
from app.services.file_validation_service import FileValidationService
from app.services.storage_service import StorageService


logger = logging.getLogger(__name__)


class ECGService:
    """Business logic for ECG upload and digitization."""

    @staticmethod
    def _write_status(
        metadata_dir: Path,
        *,
        ecg_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        """
        Persist current processing status.

        This is filesystem-based for now.
        Later this can move to MongoDB/PostgreSQL without
        changing the API/service flow significantly.
        """

        status_file = metadata_dir / "status.json"

        data = {
            "ecg_id": ecg_id,
            "status": status,
        }

        if error:
            data["error"] = error

        status_file.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _cleanup_failed_processing(
        signal_dir: Path,
        metadata_dir: Path,
    ) -> None:
        """
        Remove partial processing outputs.

        Original uploaded image is intentionally NOT removed.
        """

        if signal_dir.exists():
            shutil.rmtree(signal_dir, ignore_errors=True)

        # Keep status.json so we know that processing failed.
        for path in metadata_dir.iterdir() if metadata_dir.exists() else []:
            if path.name != "status.json":
                try:
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path, ignore_errors=True)
                except OSError as exc:
                    logger.warning(
                        "Failed to clean metadata path %s: %s",
                        path,
                        exc,
                    )

    @staticmethod
    async def upload_ecg(file: UploadFile):

        # --------------------------------
        # 1. Validate uploaded file
        # --------------------------------

        content = await FileValidationService.validate(file)

        # --------------------------------
        # 2. Generate unique ECG ID
        # --------------------------------

        ecg_id = StorageService.generate_ecg_id()

        signal_dir = settings.SIGNALS_DIR / ecg_id
        metadata_dir = settings.METADATA_DIR / ecg_id

        try:
            # --------------------------------
            # 3. Create directories
            # --------------------------------

            signal_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            metadata_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            # --------------------------------
            # 4. Initial status
            # --------------------------------

            ECGService._write_status(
                metadata_dir,
                ecg_id=ecg_id,
                status="pending",
            )

            # --------------------------------
            # 5. Save original image
            # --------------------------------

            original_path = await StorageService.save_original(
                file=file,
                ecg_id=ecg_id,
                content=content,
            )

            # --------------------------------
            # 6. Mark processing
            # --------------------------------

            ECGService._write_status(
                metadata_dir,
                ecg_id=ecg_id,
                status="processing",
            )

            logger.info(
                "Starting ECG processing: %s",
                ecg_id,
            )

            # --------------------------------
            # 7. Run digitization
            # --------------------------------

            digitization_result = await DigitizerService.digitize(
                image_path=Path(original_path),
                output_dir=signal_dir,
                output_name=ecg_id,
            )

            # --------------------------------
            # 8. Move metadata
            # --------------------------------

            worker_metadata = (
                signal_dir / f"{ecg_id}_metadata.json"
            )

            final_metadata = (
                metadata_dir / "metadata.json"
            )

            if worker_metadata.exists():
                worker_metadata.replace(final_metadata)

            # --------------------------------
            # 9. Verify required outputs
            # --------------------------------

            waveform_path = (
                signal_dir
                / f"{ecg_id}_timeseries_canonical.csv"
            )

            digital_ecg_path = (
                signal_dir
                / f"{ecg_id}.png"
            )

            if not waveform_path.exists():
                raise RuntimeError(
                    "Digitizer completed but waveform output was not generated."
                )

            # --------------------------------
            # 10. Mark completed
            # --------------------------------

            ECGService._write_status(
                metadata_dir,
                ecg_id=ecg_id,
                status="completed",
            )

            logger.info(
                "ECG processing completed: %s",
                ecg_id,
            )

            # --------------------------------
            # 11. Return response
            # --------------------------------

            return {
                "ecg_id": ecg_id,
                "status": "digitized",
                "original_filename": file.filename,
                "layout": digitization_result.get(
                    "lead_layout"
                ),
                "matching_cost": digitization_result.get(
                    "matching_cost"
                ),
                "extracted_leads": digitization_result.get(
                    "extracted_leads",
                    [],
                ),
                "sample_count": digitization_result.get(
                    "sample_count",
                    0,
                ),
                "waveform": {
                    "format": "csv",
                    "available": waveform_path.exists(),
                },
                "digital_ecg": {
                    "format": "png",
                    "available": digital_ecg_path.exists(),
                },
            }

        except Exception as exc:

            logger.exception(
                "ECG processing failed: %s",
                ecg_id,
            )

            # Keep original image.
            # Remove incomplete processing artifacts.
            ECGService._cleanup_failed_processing(
                signal_dir=signal_dir,
                metadata_dir=metadata_dir,
            )

            ECGService._write_status(
                metadata_dir,
                ecg_id=ecg_id,
                status="failed",
                error="ECG processing failed.",
            )

            # Important:
            # Don't expose internal exception details to client.
            raise RuntimeError(
                "ECG processing failed. Please try again."
            ) from exc