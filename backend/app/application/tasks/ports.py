from typing import Protocol
from uuid import UUID

from .dto import AttemptFeedback, EvaluationTaskView, LearnerTaskView, TeacherTaskView


class TaskRepository(Protocol):
    async def lesson_is_owned_by(self, *, lesson_id: UUID, author_id: UUID) -> bool: ...

    async def create_task(
        self,
        *,
        lesson_id: UUID,
        task_type: str,
        position: int,
        prompt: str,
        prompt_media_id: UUID | None,
        explanation: str,
        result_media_id: UUID | None,
        options: list[dict[str, object]],
        accepted_answers: list[str],
    ) -> TeacherTaskView: ...

    async def get_teacher_task(self, task_id: UUID) -> TeacherTaskView | None: ...

    async def list_teacher_tasks(self, course_id: UUID) -> list[TeacherTaskView]: ...

    async def list_learner_tasks(self, lesson_id: UUID) -> list[LearnerTaskView] | None: ...

    async def get_evaluation_task(self, task_id: UUID) -> EvaluationTaskView | None: ...

    async def create_attempt(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        selected_option_ids: list[UUID] | None,
        answer_text: str | None,
        correct: bool,
    ) -> AttemptFeedback: ...


class TaskTransaction(Protocol):
    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
