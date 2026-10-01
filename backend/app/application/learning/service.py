from uuid import UUID

from app.application.common.errors import ConflictError, NotFoundError

from .dto import CourseProgressView
from .ports import LearningRepository, LearningTransaction


class LearningService:
    def __init__(self, *, learning: LearningRepository, transaction: LearningTransaction) -> None:
        self._learning = learning
        self._transaction = transaction

    async def enroll_or_start(self, *, user_id: UUID, course_id: UUID) -> CourseProgressView:
        progress = await self._learning.enroll(user_id=user_id, course_id=course_id)
        await self._transaction.commit()
        return progress

    async def progress(self, *, user_id: UUID, course_id: UUID) -> CourseProgressView:
        progress = await self._learning.course_progress(user_id=user_id, course_id=course_id)
        if progress is None:
            raise NotFoundError("Enrolled course not found")
        return progress

    async def outline(self, *, user_id: UUID, course_id: UUID) -> CourseProgressView:
        outline = await self._learning.course_outline(user_id=user_id, course_id=course_id)
        if outline is None:
            raise NotFoundError("Enrolled course not found")
        return outline

    async def ensure_lesson_access(self, *, user_id: UUID, lesson_id: UUID) -> None:
        try:
            await self._learning.require_lesson_access(user_id=user_id, lesson_id=lesson_id)
        except LookupError as error:
            raise NotFoundError("Lesson not found") from error
        except PermissionError as error:
            raise ConflictError(str(error)) from error
