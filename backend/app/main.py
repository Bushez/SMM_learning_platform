from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .application.common.errors import ApplicationError
from .bootstrap.resources import InfrastructureResources
from .infrastructure.config import Settings, get_settings
from .infrastructure.logging import configure_logging
from .presentation.api.errors import (
    application_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .presentation.api.health import router as health_router
from .presentation.api.middleware import RequestContextMiddleware
from .presentation.api.v1 import api_v1_router


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(
        app_settings.log_level,
        json_logs=app_settings.app_env == "production",
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        resources = InfrastructureResources.create(app_settings)
        application.state.resources = resources
        yield
        await resources.close()

    application = FastAPI(
        title=app_settings.app_name,
        description="Backend API for courses, learning progress, and gamification.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    application.state.settings = app_settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    application.add_middleware(RequestContextMiddleware)
    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(ApplicationError, application_exception_handler)
    application.include_router(health_router)
    application.include_router(api_v1_router, prefix=app_settings.api_v1_prefix)
    return application


app = create_app()
