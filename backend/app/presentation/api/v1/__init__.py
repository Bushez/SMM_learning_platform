from fastapi import APIRouter

from .auth import router as auth_router
from .courses import catalog_router, teacher_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(catalog_router)
api_v1_router.include_router(teacher_router)

__all__ = ["api_v1_router"]
