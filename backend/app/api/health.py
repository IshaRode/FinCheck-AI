"""
Health check route for FinCheck AI API.
Provides a lightweight application-level health check endpoint.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["System"])


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Application health status")
    service: str = Field(default="FinCheck AI API", description="Service name")


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic API Health Check",
    description="Lightweight application-level health check verifying service status.",
)
@router.get(
    "/api/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def get_health() -> HealthResponse:
    """Returns basic application health status."""
    return HealthResponse(
        status="healthy",
        service="FinCheck AI API",
    )
