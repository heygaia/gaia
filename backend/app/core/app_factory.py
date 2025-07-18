"""
Application factory for the GAIA FastAPI application.

This module provides functions to create and configure the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router.health import router as health_router
from app.api.v1.routes import router as api_router
from app.config.settings import settings
from app.core.lifespan import lifespan
from app.core.middleware import configure_middleware


def create_app() -> FastAPI:
    """
    Create and configure a FastAPI application instance.

    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        lifespan=lifespan,
        title="GAIA API",
        description="Backend for General-purpose AI assistant (GAIA)",
        contact={
            "name": "Aryan Randeriya",
            "url": "http://aryanranderiya.com",
            "email": "aryan@heygaia.io",
        },
        docs_url=None if settings.ENV == "production" else "/docs",
        redoc_url=None if settings.ENV == "production" else "/redoc",
    )

    configure_middleware(app)

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(health_router)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    return app
