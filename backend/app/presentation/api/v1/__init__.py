from fastapi import APIRouter

from .auth import router as auth_router
from .courses import catalog_router, teacher_router
from .media import router as media_router
from .progress import router as progress_router
from .tasks import learning_router
from .tasks import teacher_router as task_teacher_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(catalog_router)
api_v1_router.include_router(teacher_router)
api_v1_router.include_router(media_router)
api_v1_router.include_router(progress_router)
api_v1_router.include_router(task_teacher_router)
api_v1_router.include_router(learning_router)

__all__ = ["api_v1_router"]
