from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.tasks.dto import (
    AttemptFeedback,
    EvaluationTaskView,
    LearnerTaskOptionView,
    LearnerTaskView,
    OptionFeedback,
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
        answer_feedback_text: str | None,
        answer_feedback_media_id: UUID | None,
        options: list[dict[str, object]],
        accepted_answers: list[str],
    ) -> TeacherTaskView:
        next_position = (
            await self._session.scalar(
                select(func.coalesce(func.max(TaskModel.position), 0)).where(
                    TaskModel.lesson_id == lesson_id
                )
            )
            or 0
        ) + 1
        task = TaskModel(
            lesson_id=lesson_id,
            task_type=task_type,
            position=next_position,
            prompt=prompt,
            prompt_media_id=prompt_media_id,
            answer_feedback_text=answer_feedback_text,
            answer_feedback_media_id=answer_feedback_media_id,
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
                feedback_text=option.get("feedback_text"),
                feedback_media_id=option.get("feedback_media_id"),
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
            answer_feedback_text=task.answer_feedback_text,
            answer_feedback_media_id=task.answer_feedback_media_id,
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
            answer_feedback_text=task.answer_feedback_text,
            answer_feedback_media_id=task.answer_feedback_media_id,
            options=tuple(_editor_option(option) for option in options),
            accepted_answers=tuple(answers),
        )

    async def has_learner_progress(self, task_id: UUID) -> bool:
        from ..models import UserTaskProgressModel

        return (
            await self._session.scalar(
                select(UserTaskProgressModel.task_id)
                .where(UserTaskProgressModel.task_id == task_id)
                .limit(1)
            )
            is not None
        )

    async def replace_task(
        self,
        *,
        task_id: UUID,
        task_type: str,
        position: int,
        prompt: str,
        prompt_media_id: UUID | None,
        answer_feedback_text: str | None,
        answer_feedback_media_id: UUID | None,
        options: list[dict[str, object]],
        accepted_answers: list[str],
    ) -> TeacherTaskView:
        task = await self._session.get(TaskModel, task_id, with_for_update=True)
        if task is None:
            raise RuntimeError("Task was removed during update")
        await self._session.execute(
            delete(TaskOptionModel).where(TaskOptionModel.task_id == task_id)
        )
        await self._session.execute(
            delete(TaskAcceptedAnswerModel).where(TaskAcceptedAnswerModel.task_id == task_id)
        )
        task.task_type = task_type
        task.position = position
        task.prompt = prompt
        task.prompt_media_id = prompt_media_id
        task.answer_feedback_text = answer_feedback_text
        task.answer_feedback_media_id = answer_feedback_media_id
        self._session.add_all(
            [TaskOptionModel(task_id=task_id, **option) for option in options]
            + [
                TaskAcceptedAnswerModel(task_id=task_id, normalized_value=value)
                for value in accepted_answers
            ]
        )
        await self._session.flush()
        updated = await self.get_teacher_task(task_id)
        if updated is None:
            raise RuntimeError("Task disappeared during update")
        return updated

    async def delete_task(self, task_id: UUID) -> None:
        await self._session.execute(delete(TaskModel).where(TaskModel.id == task_id))

    async def move_task(self, task_id: UUID, position: int) -> TeacherTaskView:
        task = await self._session.get(TaskModel, task_id, with_for_update=True)
        if task is None:
            raise RuntimeError("Task was removed during reorder")
        siblings = list(
            await self._session.scalars(
                select(TaskModel)
                .where(TaskModel.lesson_id == task.lesson_id)
                .order_by(TaskModel.position)
                .with_for_update()
            )
        )
        ordered = [item for item in siblings if item.id != task_id]
        target = max(1, min(position, len(siblings)))
        ordered.insert(target - 1, task)
        for index, item in enumerate(ordered, start=1):
            item.position = -index
        await self._session.flush()
        for index, item in enumerate(ordered, start=1):
            item.position = index
        await self._session.flush()
        updated = await self.get_teacher_task(task_id)
        if updated is None:
            raise RuntimeError("Task disappeared during reorder")
        return updated

    async def list_teacher_tasks(self, course_id: UUID) -> list[TeacherTaskView]:
        task_ids = list(
            await self._session.scalars(
                select(TaskModel.id)
                .join(LessonModel, TaskModel.lesson_id == LessonModel.id)
                .join(CourseModuleModel, LessonModel.module_id == CourseModuleModel.id)
                .where(CourseModuleModel.course_id == course_id)
                .order_by(CourseModuleModel.position, LessonModel.position, TaskModel.position)
            )
        )
        tasks = [await self.get_teacher_task(task_id) for task_id in task_ids]
        return [task for task in tasks if task is not None]

    async def list_learner_tasks(self, lesson_id: UUID) -> list[LearnerTaskView] | None:
        lesson = await self._session.scalar(
            select(LessonModel.id)
            .join(CourseModuleModel, LessonModel.module_id == CourseModuleModel.id)
            .join(CourseModel, CourseModuleModel.course_id == CourseModel.id)
            .where(
                LessonModel.id == lesson_id,
                CourseModel.status.in_([CourseStatus.PUBLISHED.value, CourseStatus.ARCHIVED.value]),
            )
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
            .where(
                TaskModel.id == task_id,
                CourseModel.status.in_([CourseStatus.PUBLISHED.value, CourseStatus.ARCHIVED.value]),
            )
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
            lesson_id=task.lesson_id,
            task_type=TaskType(task.task_type),
            option_ids=tuple(option.id for option in options),
            correct_option_ids=tuple(option.id for option in options if option.is_correct),
            option_feedback=tuple(
                OptionFeedback(option.id, option.feedback_text, option.feedback_media_id)
                for option in options
            ),
            accepted_answers=tuple(answers),
            answer_feedback=OptionFeedback(
                task.id, task.answer_feedback_text, task.answer_feedback_media_id
            ),
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
            correct_option_ids=tuple(option.id for option in options if option.is_correct),
            option_feedback=tuple(
                OptionFeedback(option.id, option.feedback_text, option.feedback_media_id)
                for option in options
                if selected_option_ids is not None and option.id in selected_option_ids
            ),
            answer_feedback=OptionFeedback(
                task.id, task.answer_feedback_text, task.answer_feedback_media_id
            )
            if selected_option_ids is None
            else None,
            created_at=model.created_at or datetime.now(UTC),
        )


def _editor_option(model: TaskOptionModel) -> TaskOptionEditorView:
    return TaskOptionEditorView(
        id=model.id,
        text=model.text,
        media_id=model.media_id,
        position=model.position,
        is_correct=model.is_correct,
        feedback_text=model.feedback_text,
        feedback_media_id=model.feedback_media_id,
    )
