from typing import Protocol
from uuid import UUID

from .dto import CompletionUpdate, CourseProgressView


class LearningRepository(Protocol):
    async def enroll(self, *, user_id: UUID, course_id: UUID) -> CourseProgressView: ...

    async def course_progress(
        self, *, user_id: UUID, course_id: UUID
    ) -> CourseProgressView | None: ...

    async def course_outline(
        self, *, user_id: UUID, course_id: UUID
    ) -> CourseProgressView | None: ...

    async def require_lesson_access(self, *, user_id: UUID, lesson_id: UUID) -> None: ...

    async def record_task_completion(self, *, user_id: UUID, task_id: UUID) -> CompletionUpdate: ...


class LearningTransaction(Protocol):
    async def commit(self) -> None: ...
