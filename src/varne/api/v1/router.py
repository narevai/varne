from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from varne.config import get_settings

router = APIRouter()


class ResponseHealth(BaseModel):
    status: str
    environment: str
    version: str


@router.get("/health", response_model=ResponseHealth)
async def health_check() -> ResponseHealth:
    settings = get_settings()
    logger.debug("Health check requested")
    return ResponseHealth(
        status="healthy", environment=settings.environment, version=settings.api_version
    )
