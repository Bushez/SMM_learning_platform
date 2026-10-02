from collections import defaultdict
from typing import cast
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.learning.dto import (
    CompletionUpdate,
    CourseProgressView,
    LessonProgressView,
    ModuleProgressView,
)
from app.domain.courses import CourseStatus
from app.domain.learning import is_lesson_unlocked

from ..models import (
    CourseEnrollmentModel,
    CourseModel,
    CourseModuleModel,
    LessonModel,
    TaskModel,
    UserTaskProgressModel,
)

type LessonRow = tuple[UUID, str, int, UUID, str, int, int, int]


class SqlAlchemyLearningRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enroll(self, *, user_id: UUID, course_id: UUID) -> CourseProgressView:
        course = await self._session.scalar(
            select(CourseModel).where(
                CourseModel.id == course_id, CourseModel.status == CourseStatus.PUBLISHED.value
            )
        )
        if course is None:
            raise LookupError("Published course not found")
        await self._session.execute(
            insert(CourseEnrollmentModel)
            .values(user_id=user_id, course_id=course_id)
            .on_conflict_do_nothing(index_elements=["user_id", "course_id"])
        )
        return await self._course_progress(user_id=user_id, course_id=course_id, enrolled=True)

    async def course_progress(self, *, user_id: UUID, course_id: UUID) -> CourseProgressView | None:
        enrolled = await self._session.get(CourseEnrollmentModel, (user_id, course_id))
        if enrolled is None:
            return None
        course = await self._session.scalar(select(CourseModel).where(CourseModel.id == course_id))
        if course is None:
            return None
        return await self._course_progress(user_id=user_id, course_id=course_id, enrolled=True)

    async def course_outline(self, *, user_id: UUID, course_id: UUID) -> CourseProgressView | None:
        base_progress = await self.course_progress(user_id=user_id, course_id=course_id)
        if base_progress is None:
            return None
        lesson_rows = await self._lesson_rows(user_id=user_id, course_id=course_id)
        lessons_by_module: dict[UUID, list[LessonProgressView]] = defaultdict(list)
        module_details: dict[UUID, tuple[str, int]] = {}
        previous_completion: list[bool] = []
        for (
            module_id,
            module_title,
            module_position,
            lesson_id,
            lesson_title,
            lesson_position,
            total,
            completed,
        ) in lesson_rows:
            lesson_completed = total > 0 and total == completed
            lessons_by_module[module_id].append(
                LessonProgressView(
                    id=lesson_id,
                    module_id=module_id,
                    title=lesson_title,
                    position=lesson_position,
                    total_tasks=total,
                    completed_tasks=completed,
                    completed=lesson_completed,
                    unlocked=is_lesson_unlocked(prior_lesson_completion=previous_completion),
                )
            )
            previous_completion.append(lesson_completed)
            module_details[module_id] = (module_title, module_position)
        modules = tuple(
            ModuleProgressView(
                id=module_id,
                title=module_details[module_id][0],
                position=module_details[module_id][1],
                lessons=tuple(lessons),
                completed=bool(lessons) and all(lesson.completed for lesson in lessons),
            )
            for module_id, lessons in lessons_by_module.items()
        )
        return CourseProgressView(
            course_id=base_progress.course_id,
            enrolled=True,
            total_tasks=base_progress.total_tasks,
            completed_tasks=base_progress.completed_tasks,
            progress_percent=base_progress.progress_percent,
            completed=base_progress.completed,
            modules=modules,
        )

    async def require_lesson_access(self, *, user_id: UUID, lesson_id: UUID) -> None:
        course_id = await self._session.scalar(
            select(CourseModel.id)
            .join(CourseModuleModel, CourseModuleModel.course_id == CourseModel.id)
            .join(LessonModel, LessonModel.module_id == CourseModuleModel.id)
            .where(
                LessonModel.id == lesson_id,
                CourseModel.status.in_([CourseStatus.PUBLISHED.value, CourseStatus.ARCHIVED.value]),
            )
        )
        if course_id is None:
            raise LookupError("Published lesson not found")
        outline = await self.course_outline(user_id=user_id, course_id=course_id)
        if outline is None:
            raise PermissionError("Course enrollment is required")
        for module in outline.modules:
            for lesson in module.lessons:
                if lesson.id == lesson_id:
                    if not lesson.unlocked:
                        raise PermissionError("Complete previous lessons to unlock this lesson")
                    return
        raise LookupError("Lesson not found")

    async def record_task_completion(self, *, user_id: UUID, task_id: UUID) -> CompletionUpdate:
        task_context = await self._session.execute(
            select(TaskModel.lesson_id, CourseModuleModel.id, CourseModel.id)
            .join(LessonModel, TaskModel.lesson_id == LessonModel.id)
            .join(CourseModuleModel, LessonModel.module_id == CourseModuleModel.id)
            .join(CourseModel, CourseModuleModel.course_id == CourseModel.id)
            .where(TaskModel.id == task_id)
        )
        row = task_context.one_or_none()
        if row is None:
            raise LookupError("Task not found")
        lesson_id, module_id, course_id = row
        result = await self._session.execute(
            insert(UserTaskProgressModel)
            .values(user_id=user_id, task_id=task_id)
            .on_conflict_do_nothing(index_elements=["user_id", "task_id"])
            .returning(UserTaskProgressModel.task_id)
        )
        first_completion = result.scalar_one_or_none() is not None
        outline = await self.course_outline(user_id=user_id, course_id=course_id)
        if outline is None:
            raise PermissionError("Course enrollment is required")
        lesson_completed = False
        module_completed = False
        for module in outline.modules:
            if module.id == module_id:
                module_completed = module.completed
                lesson_completed = next(
                    (lesson.completed for lesson in module.lessons if lesson.id == lesson_id), False
                )
                break
        return CompletionUpdate(
            course_id=course_id,
            first_task_completion=first_completion,
            lesson_completed=lesson_completed,
            module_completed=module_completed,
            course_completed=outline.completed,
            course_progress_percent=outline.progress_percent,
        )

    async def _course_progress(
        self, *, user_id: UUID, course_id: UUID, enrolled: bool
    ) -> CourseProgressView:
        total, completed = (
            await self._session.execute(
                select(
                    func.count(TaskModel.id),
                    func.count(UserTaskProgressModel.task_id),
                )
                .select_from(CourseModuleModel)
                .join(LessonModel, LessonModel.module_id == CourseModuleModel.id)
                .join(TaskModel, TaskModel.lesson_id == LessonModel.id)
                .outerjoin(
                    UserTaskProgressModel,
                    and_(
                        UserTaskProgressModel.task_id == TaskModel.id,
                        UserTaskProgressModel.user_id == user_id,
                    ),
                )
                .where(CourseModuleModel.course_id == course_id)
            )
        ).one()
        total_tasks = int(total)
        completed_tasks = int(completed)
        progress_percent = 0 if total_tasks == 0 else completed_tasks * 100 // total_tasks
        return CourseProgressView(
            course_id=course_id,
            enrolled=enrolled,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            progress_percent=progress_percent,
            completed=total_tasks > 0 and completed_tasks == total_tasks,
        )

    async def _lesson_rows(self, *, user_id: UUID, course_id: UUID) -> list[LessonRow]:
        rows = list(
            await self._session.execute(
                select(
                    CourseModuleModel.id,
                    CourseModuleModel.title,
                    CourseModuleModel.position,
                    LessonModel.id,
                    LessonModel.title,
                    LessonModel.position,
                    func.count(TaskModel.id),
                    func.count(UserTaskProgressModel.task_id),
                )
                .join(LessonModel, LessonModel.module_id == CourseModuleModel.id)
                .outerjoin(TaskModel, TaskModel.lesson_id == LessonModel.id)
                .outerjoin(
                    UserTaskProgressModel,
                    and_(
                        UserTaskProgressModel.task_id == TaskModel.id,
                        UserTaskProgressModel.user_id == user_id,
                    ),
                )
                .where(CourseModuleModel.course_id == course_id)
                .group_by(CourseModuleModel.id, LessonModel.id)
                .order_by(CourseModuleModel.position, LessonModel.position)
            )
        )
        return cast(list[LessonRow], rows)
