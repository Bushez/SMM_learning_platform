from collections.abc import Iterable
from uuid import UUID

from app.application.common.errors import AuthorizationError, NotFoundError, ValidationError
from app.application.media.ports import MediaRepository
from app.domain.courses import TaskType
from app.domain.learning import evaluate_choice, evaluate_text_answer, normalize_text_answer

from .dto import AttemptFeedback, LearnerTaskView, TeacherTaskView
from .ports import TaskRepository, TaskTransaction


class TaskService:
    def __init__(
        self,
        *,
        tasks: TaskRepository,
        media: MediaRepository,
        transaction: TaskTransaction,
    ) -> None:
        self._tasks = tasks
        self._media = media
        self._transaction = transaction

    async def create_task(
        self,
        *,
        author_id: UUID,
        lesson_id: UUID,
        task_type: TaskType,
        position: int,
        prompt: str,
        prompt_media_id: UUID | None,
        explanation: str,
        result_media_id: UUID | None,
        options: list[dict[str, object]],
        accepted_answers: list[str],
    ) -> TeacherTaskView:
        if not await self._tasks.lesson_is_owned_by(lesson_id=lesson_id, author_id=author_id):
            raise AuthorizationError("You do not own this lesson")
        self._validate_definition(
            task_type=task_type, options=options, accepted_answers=accepted_answers
        )
        await self._validate_media_ownership(
            author_id=author_id,
            media_ids=self._media_ids(prompt_media_id, result_media_id, options),
        )
        task = await self._tasks.create_task(
            lesson_id=lesson_id,
            task_type=task_type.value,
            position=position,
            prompt=prompt.strip(),
            prompt_media_id=prompt_media_id,
            explanation=explanation.strip(),
            result_media_id=result_media_id,
            options=options,
            accepted_answers=[normalize_text_answer(value) for value in accepted_answers],
        )
        await self._transaction.commit()
        return task

    async def teacher_task(self, *, author_id: UUID, task_id: UUID) -> TeacherTaskView:
        task = await self._tasks.get_teacher_task(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        if not await self._tasks.lesson_is_owned_by(lesson_id=task.lesson_id, author_id=author_id):
            raise AuthorizationError("You do not own this task")
        return task

    async def learner_tasks(self, *, lesson_id: UUID) -> list[LearnerTaskView]:
        tasks = await self._tasks.list_learner_tasks(lesson_id)
        if tasks is None:
            raise NotFoundError("Published lesson not found")
        return tasks

    async def submit_choice_attempt(
        self, *, user_id: UUID, task_id: UUID, selected_option_ids: list[UUID]
    ) -> AttemptFeedback:
        task = await self._evaluation_task(task_id)
        if task.task_type is TaskType.TEXT_INPUT:
            raise ValidationError("This task requires a text answer")
        if task.task_type is TaskType.SINGLE_CHOICE and len(selected_option_ids) != 1:
            raise ValidationError("Single choice tasks require exactly one selected option")
        if len(selected_option_ids) != len(set(selected_option_ids)):
            raise ValidationError("Selected option IDs must be unique")
        if not set(selected_option_ids).issubset(task.option_ids):
            raise ValidationError("Selected option does not belong to this task")
        correct = evaluate_choice(
            selected_option_ids=selected_option_ids, correct_option_ids=task.correct_option_ids
        )
        attempt = await self._tasks.create_attempt(
            user_id=user_id,
            task_id=task.id,
            selected_option_ids=selected_option_ids,
            answer_text=None,
            correct=correct,
        )
        await self._transaction.commit()
        return attempt

    async def submit_text_attempt(
        self, *, user_id: UUID, task_id: UUID, answer_text: str
    ) -> AttemptFeedback:
        task = await self._evaluation_task(task_id)
        if task.task_type is not TaskType.TEXT_INPUT:
            raise ValidationError("This task requires choice options")
        correct = evaluate_text_answer(answer=answer_text, accepted_answers=task.accepted_answers)
        attempt = await self._tasks.create_attempt(
            user_id=user_id,
            task_id=task.id,
            selected_option_ids=None,
            answer_text=answer_text.strip(),
            correct=correct,
        )
        await self._transaction.commit()
        return attempt

    async def _evaluation_task(self, task_id: UUID):
        task = await self._tasks.get_evaluation_task(task_id)
        if task is None:
            raise NotFoundError("Published task not found")
        return task

    async def _validate_media_ownership(
        self, *, author_id: UUID, media_ids: Iterable[UUID]
    ) -> None:
        for media_id in media_ids:
            if not await self._media.is_owned_by(media_id=media_id, owner_id=author_id):
                raise ValidationError("Task media must be uploaded by this teacher")

    @staticmethod
    def _media_ids(
        prompt_media_id: UUID | None, result_media_id: UUID | None, options: list[dict[str, object]]
    ) -> tuple[UUID, ...]:
        option_media_ids = [value for option in options if (value := option.get("media_id"))]
        return tuple(
            media_id
            for media_id in [prompt_media_id, result_media_id, *option_media_ids]
            if isinstance(media_id, UUID)
        )

    @staticmethod
    def _validate_definition(
        *, task_type: TaskType, options: list[dict[str, object]], accepted_answers: list[str]
    ) -> None:
        if task_type is TaskType.TEXT_INPUT:
            if options:
                raise ValidationError("Text input tasks cannot contain options")
            if not accepted_answers or any(not value.strip() for value in accepted_answers):
                raise ValidationError("Text input tasks require at least one accepted answer")
            return
        if accepted_answers:
            raise ValidationError("Choice tasks cannot contain accepted text answers")
        if len(options) < 2:
            raise ValidationError("Choice tasks require at least two options")
        positions = [option.get("position") for option in options]
        if len(positions) != len(set(positions)):
            raise ValidationError("Task option positions must be unique")
        for option in options:
            if not option.get("text") and not option.get("media_id"):
                raise ValidationError("Each option requires text or an image")
        correct_count = sum(option.get("is_correct") is True for option in options)
        if task_type is TaskType.SINGLE_CHOICE and correct_count != 1:
            raise ValidationError("Single choice tasks require exactly one correct option")
        if task_type is TaskType.MULTIPLE_CHOICE and correct_count < 1:
            raise ValidationError("Multiple choice tasks require at least one correct option")
