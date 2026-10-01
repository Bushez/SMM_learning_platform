from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.application.auth.dto import UserView
from app.application.learning import LearningService
from app.application.learning.dto import CourseProgressView, LessonProgressView, ModuleProgressView
from app.presentation.api.dependencies import (
    get_learning_service,
    require_authenticated_user,
)

router = APIRouter(prefix="/learning/courses", tags=["Learning"])


class LessonProgressResponse(BaseModel):
    id: UUID
    module_id: UUID
    title: str
    position: int
    total_tasks: int
    completed_tasks: int
    completed: bool
    unlocked: bool

    @classmethod
    def from_view(cls, lesson: LessonProgressView) -> "LessonProgressResponse":
        return cls(
            id=lesson.id,
            module_id=lesson.module_id,
            title=lesson.title,
            position=lesson.position,
            total_tasks=lesson.total_tasks,
            completed_tasks=lesson.completed_tasks,
            completed=lesson.completed,
            unlocked=lesson.unlocked,
        )


class ModuleProgressResponse(BaseModel):
    id: UUID
    title: str
    position: int
    lessons: list[LessonProgressResponse]
    completed: bool

    @classmethod
    def from_view(cls, module: ModuleProgressView) -> "ModuleProgressResponse":
        return cls(
            id=module.id,
            title=module.title,
            position=module.position,
            lessons=[LessonProgressResponse.from_view(lesson) for lesson in module.lessons],
            completed=module.completed,
        )


class CourseProgressResponse(BaseModel):
    course_id: UUID
    enrolled: bool
    total_tasks: int
    completed_tasks: int
    progress_percent: int
    completed: bool
    modules: list[ModuleProgressResponse]

    @classmethod
    def from_view(cls, progress: CourseProgressView) -> "CourseProgressResponse":
        return cls(
            course_id=progress.course_id,
            enrolled=progress.enrolled,
            total_tasks=progress.total_tasks,
            completed_tasks=progress.completed_tasks,
            progress_percent=progress.progress_percent,
            completed=progress.completed,
            modules=[ModuleProgressResponse.from_view(module) for module in progress.modules],
        )


@router.post(
    "/{course_id}/enroll",
    response_model=CourseProgressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start or resume a published course",
    operation_id="enrollInCourse",
)
async def enroll_in_course(
    course_id: UUID,
    user: UserView = Depends(require_authenticated_user),
    service: LearningService = Depends(get_learning_service),
) -> CourseProgressResponse:
    return CourseProgressResponse.from_view(
        await service.enroll_or_start(user_id=user.id, course_id=course_id)
    )


@router.get(
    "/{course_id}/progress",
    response_model=CourseProgressResponse,
    summary="Get aggregate progress for an enrolled course",
    operation_id="getCourseProgress",
)
async def get_course_progress(
    course_id: UUID,
    user: UserView = Depends(require_authenticated_user),
    service: LearningService = Depends(get_learning_service),
) -> CourseProgressResponse:
    return CourseProgressResponse.from_view(
        await service.progress(user_id=user.id, course_id=course_id)
    )


@router.get(
    "/{course_id}/outline",
    response_model=CourseProgressResponse,
    summary="Get enrolled course outline with lesson unlock states",
    operation_id="getCourseLearningOutline",
)
async def get_course_outline(
    course_id: UUID,
    user: UserView = Depends(require_authenticated_user),
    service: LearningService = Depends(get_learning_service),
) -> CourseProgressResponse:
    return CourseProgressResponse.from_view(
        await service.outline(user_id=user.id, course_id=course_id)
    )
