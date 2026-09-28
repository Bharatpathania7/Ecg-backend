from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.ecg import router as ecg_router
from app.core.config import settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):

    setup_logging()

    settings.ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    settings.SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    settings.METADATA_DIR.mkdir(parents=True, exist_ok=True)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend for ECG image digitization and signal extraction.",
    lifespan=lifespan,
)


app.include_router(
    ecg_router,
    prefix="/api/v1",
)


@app.get("/health")
async def health_check():

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }