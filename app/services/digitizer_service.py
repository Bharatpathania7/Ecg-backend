import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from app.core.config import settings


logger = logging.getLogger(__name__)


class DigitizerService:
    """
    Manages the long-running ECG digitizer worker.

    FastAPI:
        Python 3.11

    Worker:
        Python 3.12 + PyTorch + CUDA
    """

    _process: subprocess.Popen | None = None
    _lock = asyncio.Lock()

    # --------------------------------
    # Worker startup
    # --------------------------------

    @classmethod
    async def start(cls) -> None:
        """Start the ECG digitizer worker."""

        if cls._process is not None:
            if cls._process.poll() is None:
                return

            logger.warning(
                "Existing digitizer worker is no longer running."
            )

            cls._process = None

        python_path = settings.DIGITIZER_PYTHON
        worker_path = settings.DIGITIZER_WORKER
        working_directory = settings.DIGITIZER_ROOT

        if not python_path.exists():
            raise FileNotFoundError(
                f"Digitizer Python not found: {python_path}"
            )

        if not worker_path.exists():
            raise FileNotFoundError(
                f"Digitizer worker not found: {worker_path}"
            )

        logger.info(
            "Starting ECG digitizer worker..."
        )

        process = subprocess.Popen(
            [
                str(python_path),
                str(worker_path),
            ],
            cwd=str(working_directory),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            bufsize=1,
        )

        cls._process = process

        try:
            if process.stdout is None:
                raise RuntimeError(
                    "Digitizer worker stdout is unavailable."
                )

            ready_line = await asyncio.to_thread(
                process.stdout.readline
            )

            if not ready_line:
                raise RuntimeError(
                    "Digitizer worker exited during startup."
                )

            result = json.loads(
                ready_line.strip()
            )

            if (
                result.get("event") != "ready"
                or result.get("status") != "ready"
            ):
                raise RuntimeError(
                    f"Digitizer worker failed to start: {result}"
                )

            logger.info(
                "ECG digitizer worker is ready."
            )

        except Exception:
            await cls.stop()
            raise

    # --------------------------------
    # Worker stop
    # --------------------------------

    @classmethod
    async def stop(cls) -> None:
        """Gracefully stop the ECG digitizer worker."""

        process = cls._process

        if process is None:
            return

        logger.info(
            "Stopping ECG digitizer worker..."
        )

        try:

            if process.poll() is None:

                if process.stdin:

                    request = {
                        "command": "shutdown"
                    }

                    try:
                        process.stdin.write(
                            json.dumps(request) + "\n"
                        )
                        process.stdin.flush()
                        process.stdin.close()

                    except (BrokenPipeError, OSError):
                        logger.warning(
                            "Worker stdin already closed."
                        )

                await asyncio.to_thread(
                    process.wait,
                    10,
                )

        except subprocess.TimeoutExpired:

            logger.warning(
                "Worker did not stop gracefully. "
                "Terminating process."
            )

            process.terminate()

            try:

                await asyncio.to_thread(
                    process.wait,
                    5,
                )

            except subprocess.TimeoutExpired:

                logger.warning(
                    "Worker did not terminate. "
                    "Killing process."
                )

                process.kill()

                await asyncio.to_thread(
                    process.wait
                )

        except Exception as exc:

            logger.warning(
                "Worker shutdown failed: %s",
                exc,
            )

            if process.poll() is None:
                process.kill()

        finally:

            cls._process = None

        logger.info(
            "ECG digitizer worker stopped."
        )

    # --------------------------------
    # Worker restart
    # --------------------------------

    @classmethod
    async def restart(cls) -> None:
        """Restart the digitizer worker."""

        logger.warning(
            "Restarting ECG digitizer worker..."
        )

        await cls.stop()
        await cls.start()

        logger.info(
            "ECG digitizer worker restarted successfully."
        )

    # --------------------------------
    # Digitization
    # --------------------------------

    @classmethod
    async def digitize(
        cls,
        image_path: Path,
        output_dir: Path,
        output_name: str,
    ) -> dict[str, Any]:

        async with cls._lock:

            process = cls._process

            if process is None:
                raise RuntimeError(
                    "Digitizer worker is not running."
                )

            if process.poll() is not None:

                logger.error(
                    "Digitizer worker has stopped."
                )

                cls._process = None

                raise RuntimeError(
                    "Digitizer worker has stopped."
                )

            if process.stdin is None:
                raise RuntimeError(
                    "Digitizer worker stdin is unavailable."
                )

            if process.stdout is None:
                raise RuntimeError(
                    "Digitizer worker stdout is unavailable."
                )

            output_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            request = {
                "command": "digitize",
                "image_path": str(
                    image_path.resolve()
                ),
                "output_dir": str(
                    output_dir.resolve()
                ),
                "output_name": output_name,
            }

            logger.info(
                "Sending ECG to digitizer: %s",
                image_path.name,
            )

            try:

                process.stdin.write(
                    json.dumps(request) + "\n"
                )

                process.stdin.flush()

            except (BrokenPipeError, OSError) as exc:

                logger.error(
                    "Failed to send request to digitizer worker: %s",
                    exc,
                )

                cls._process = None

                raise RuntimeError(
                    "Digitizer worker is unavailable."
                ) from exc

            # --------------------------------
            # Wait for worker response
            # --------------------------------

            try:

                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        process.stdout.readline
                    ),
                    timeout=180,
                )

            except asyncio.TimeoutError as exc:

                logger.error(
                    "ECG digitization timed out: %s",
                    image_path.name,
                )

                # Worker is considered unhealthy.
                # Do not leave a potentially hung process alive.
                await cls._force_kill_process(process)

                raise RuntimeError(
                    "ECG digitization timed out."
                ) from exc

            # --------------------------------
            # Worker closed connection
            # --------------------------------

            if not response:

                logger.error(
                    "Digitizer worker closed connection."
                )

                cls._process = None

                raise RuntimeError(
                    "Digitizer worker closed the connection."
                )

            # --------------------------------
            # Parse response
            # --------------------------------

            try:

                result = json.loads(
                    response.strip()
                )

            except json.JSONDecodeError as exc:

                logger.error(
                    "Invalid response from digitizer worker: %s",
                    response,
                )

                raise RuntimeError(
                    "Invalid response from digitizer worker."
                ) from exc

            # --------------------------------
            # Worker reported error
            # --------------------------------

            if result.get("status") == "error":

                worker_error = result.get(
                    "error",
                    "Digitization failed.",
                )

                logger.error(
                    "Digitizer worker error: %s",
                    worker_error,
                )

                raise RuntimeError(
                    "Digitization failed."
                )

            # --------------------------------
            # Success
            # --------------------------------

            logger.info(
                "ECG digitization completed: %s",
                image_path.name,
            )

            return result

    # --------------------------------
    # Force kill
    # --------------------------------

    @classmethod
    async def _force_kill_process(
        cls,
        process: subprocess.Popen,
    ) -> None:

        logger.warning(
            "Force stopping unhealthy digitizer worker."
        )

        try:

            if process.poll() is None:
                process.kill()

                await asyncio.to_thread(
                    process.wait,
                    5,
                )

        except Exception as exc:

            logger.warning(
                "Failed to kill digitizer worker: %s",
                exc,
            )

        finally:

            if cls._process is process:
                cls._process = None