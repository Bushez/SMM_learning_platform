import asyncio
from typing import Literal

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...bootstrap.resources import InfrastructureResources

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessChecks(BaseModel):
    database: bool
    redis: bool


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: ReadinessChecks


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Returns success while the API process can handle HTTP requests.",
    operation_id="getHealth",
)
async def get_health() -> HealthResponse:
    return HealthResponse()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Dependency readiness check",
    description="Checks PostgreSQL and Redis without exposing connection details.",
    operation_id="getReadiness",
    responses={503: {"description": "At least one required dependency is unavailable."}},
)
async def get_readiness(request: Request) -> ReadinessResponse | JSONResponse:
    resources: InfrastructureResources = request.app.state.resources
    database_ready, redis_ready = await asyncio.gather(
        resources.database_is_ready(), resources.redis_is_ready()
    )
    checks = ReadinessChecks(database=database_ready, redis=redis_ready)
    if database_ready and redis_ready:
        return ReadinessResponse(status="ready", checks=checks)
    payload = ReadinessResponse(status="not_ready", checks=checks)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload.model_dump()
    )
