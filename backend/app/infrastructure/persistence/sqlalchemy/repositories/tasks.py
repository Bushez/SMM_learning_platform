from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.tasks.dto import (
    AttemptFeedback,
    EvaluationTaskView,
    LearnerTaskOptionView,
    LearnerTaskView,
    TaskOptionEditorView,
    TeacherTaskView,
)
from app.domain.courses import CourseStatus, TaskType

from ..models import (
    CourseModel,
    CourseModuleModel,
    LessonModel,
    TaskAcceptedAnswerModel,
    TaskAttemptModel,
    TaskModel,
    TaskOptionModel,
)


class SqlAlchemyTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lesson_is_owned_by(self, *, lesson_id: UUID, author_id: UUID) -> bool:
        result = await self._session.scalar(
            select(LessonModel.id)
            .join(CourseModuleModel, LessonModel.module_id == CourseModuleModel.id)
            .join(CourseModel, CourseModuleModel.course_id == CourseModel.id)
            .where(LessonModel.id == lesson_id, CourseModel.author_id == author_id)
        )
        return result is not None

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
    ) -> TeacherTaskView:
        task = TaskModel(
            lesson_id=lesson_id,
            task_type=task_type,
            position=position,
            prompt=prompt,
            prompt_media_id=prompt_media_id,
            explanation=explanation,
            result_media_id=result_media_id,
        )
        self._session.add(task)
        await self._session.flush()
        option_models = [
            TaskOptionModel(
                task_id=task.id,
                text=option.get("text"),
                media_id=option.get("media_id"),
                position=option["position"],
                is_correct=option["is_correct"],
            )
            for option in options
        ]
        answer_models = [
            TaskAcceptedAnswerModel(task_id=task.id, normalized_value=value)
            for value in accepted_answers
        ]
        self._session.add_all([*option_models, *answer_models])
        await self._session.flush()
        return TeacherTaskView(
            id=task.id,
            lesson_id=task.lesson_id,
            task_type=TaskType(task.task_type),
            position=task.position,
            prompt=task.prompt,
            prompt_media_id=task.prompt_media_id,
            explanation=task.explanation,
            result_media_id=task.result_media_id,
            options=tuple(_editor_option(option) for option in option_models),
            accepted_answers=tuple(answer.normalized_value for answer in answer_models),
        )

    async def get_teacher_task(self, task_id: UUID) -> TeacherTaskView | None:
        task = await self._session.get(TaskModel, task_id)
        if task is None:
            return None
        options = list(
            await self._session.scalars(
                select(TaskOptionModel)
                .where(TaskOptionModel.task_id == task_id)
                .order_by(TaskOptionModel.position)
            )
        )
        answers = list(
            await self._session.scalars(
                select(TaskAcceptedAnswerModel.normalized_value).where(
                    TaskAcceptedAnswerModel.task_id == task_id
                )
            )
        )
        return TeacherTaskView(
            id=task.id,
            lesson_id=task.lesson_id,
            task_type=TaskType(task.task_type),
            position=task.position,
            prompt=task.prompt,
            prompt_media_id=task.prompt_media_id,
            explanation=task.explanation,
            result_media_id=task.result_media_id,
            options=tuple(_editor_option(option) for option in options),
            accepted_answers=tuple(answers),
        )

    async def list_learner_tasks(self, lesson_id: UUID) -> list[LearnerTaskView] | None:
        lesson = await self._session.scalar(
            select(LessonModel.id)
            .join(CourseModuleModel, LessonModel.module_id == CourseModuleModel.id)
            .join(CourseModel, CourseModuleModel.course_id == CourseModel.id)
            .where(LessonModel.id == lesson_id, CourseModel.status == CourseStatus.PUBLISHED.value)
        )
        if lesson is None:
            return None
        tasks = list(
            await self._session.scalars(
                select(TaskModel)
                .where(TaskModel.lesson_id == lesson_id)
                .order_by(TaskModel.position)
            )
        )
        options = list(
            await self._session.scalars(
                select(TaskOptionModel)
                .join(TaskModel, TaskOptionModel.task_id == TaskModel.id)
                .where(TaskModel.lesson_id == lesson_id)
                .order_by(TaskOptionModel.position)
            )
        )
        options_by_task: dict[UUID, list[LearnerTaskOptionView]] = {}
        for option in options:
            options_by_task.setdefault(option.task_id, []).append(
                LearnerTaskOptionView(
                    id=option.id,
                    text=option.text,
                    media_id=option.media_id,
                    position=option.position,
                )
            )
        return [
            LearnerTaskView(
                id=task.id,
                lesson_id=task.lesson_id,
                task_type=TaskType(task.task_type),
                position=task.position,
                prompt=task.prompt,
                prompt_media_id=task.prompt_media_id,
                options=tuple(options_by_task.get(task.id, [])),
            )
            for task in tasks
        ]

    async def get_evaluation_task(self, task_id: UUID) -> EvaluationTaskView | None:
        task = await self._session.scalar(
            select(TaskModel)
            .join(LessonModel, TaskModel.lesson_id == LessonModel.id)
            .join(CourseModuleModel, LessonModel.module_id == CourseModuleModel.id)
            .join(CourseModel, CourseModuleModel.course_id == CourseModel.id)
            .where(TaskModel.id == task_id, CourseModel.status == CourseStatus.PUBLISHED.value)
        )
        if task is None:
            return None
        options = list(
            await self._session.scalars(
                select(TaskOptionModel).where(TaskOptionModel.task_id == task_id)
            )
        )
        answers = list(
            await self._session.scalars(
                select(TaskAcceptedAnswerModel.normalized_value).where(
                    TaskAcceptedAnswerModel.task_id == task_id
                )
            )
        )
        return EvaluationTaskView(
            id=task.id,
            task_type=TaskType(task.task_type),
            explanation=task.explanation,
            result_media_id=task.result_media_id,
            option_ids=tuple(option.id for option in options),
            correct_option_ids=tuple(option.id for option in options if option.is_correct),
            accepted_answers=tuple(answers),
        )

    async def create_attempt(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        selected_option_ids: list[UUID] | None,
        answer_text: str | None,
        correct: bool,
    ) -> AttemptFeedback:
        task = await self._session.get(TaskModel, task_id)
        if task is None:
            raise RuntimeError("Task disappeared before attempt persistence")
        model = TaskAttemptModel(
            user_id=user_id,
            task_id=task_id,
            selected_option_ids=[str(option_id) for option_id in selected_option_ids]
            if selected_option_ids is not None
            else None,
            answer_text=answer_text,
            correct=correct,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        options = list(
            await self._session.scalars(
                select(TaskOptionModel).where(TaskOptionModel.task_id == task_id)
            )
        )
        return AttemptFeedback(
            attempt_id=model.id,
            correct=model.correct,
            explanation=task.explanation,
            result_media_id=task.result_media_id,
            correct_option_ids=tuple(option.id for option in options if option.is_correct),
            created_at=model.created_at or datetime.now(UTC),
        )


def _editor_option(model: TaskOptionModel) -> TaskOptionEditorView:
    return TaskOptionEditorView(
        id=model.id,
        text=model.text,
        media_id=model.media_id,
        position=model.position,
        is_correct=model.is_correct,
    )
