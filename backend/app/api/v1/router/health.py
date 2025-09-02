"""
Health check routes for the GAIA FastAPI application.

This module provides routes for checking the health and status of the API.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/")
@router.get("/ping")
@router.get("/health")
@router.get("/api/v1/")
@router.get("/api/v1/ping")
def health_check():
    """
    Health check endpoint for the API.

    Returns:
        dict: Status information about the API
    """
    # Lazy import to avoid loading settings during module import
    from app.config.settings import settings

    return {
        "status": "online",
        "message": "Welcome to the GAIA API!",
        "name": "GAIA API",
        "version": "1.0.0",
        "description": "Backend for General-purpose AI assistant (GAIA)",
        "environment": settings.ENV,
        "developer": {
            "name": "Aryan Randeriya",
            "email": "aryan@heygaia.io",
            "url": "https://aryanranderiya.com",
        },
    }


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Serve favicon.ico file.

    Returns:
        FileResponse: Favicon file
    """
    return FileResponse("app/static/favicon.ico")
