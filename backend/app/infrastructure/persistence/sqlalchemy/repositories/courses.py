from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.courses.dto import CourseView, ModuleView
from app.domain.courses import CourseStatus

from ..models import CourseModel, CourseModuleModel, LessonModel, TaskModel


def _course_view(model: CourseModel) -> CourseView:
    return CourseView(
        id=model.id,
        author_id=model.author_id,
        title=model.title,
        slug=model.slug,
        description=model.description,
        cover_media_id=model.cover_media_id,
        category=model.category,
        language_code=model.language_code,
        status=CourseStatus(model.status),
    )


def _module_view(model: CourseModuleModel) -> ModuleView:
    return ModuleView(
        id=model.id,
        course_id=model.course_id,
        title=model.title,
        description=model.description,
        position=model.position,
    )


class SqlAlchemyCourseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_course(self, **kwargs: object) -> CourseView:
        model = CourseModel(**kwargs)
        self._session.add(model)
        await self._session.flush()
        return _course_view(model)

    async def get_course(self, course_id: UUID) -> CourseView | None:
        model = await self._session.get(CourseModel, course_id)
        return None if model is None else _course_view(model)

    async def get_by_slug(self, slug: str) -> CourseView | None:
        model = await self._session.scalar(select(CourseModel).where(CourseModel.slug == slug))
        return None if model is None else _course_view(model)

    async def list_published(self, *, limit: int, offset: int) -> list[CourseView]:
        result = await self._session.scalars(
            select(CourseModel)
            .where(CourseModel.status == CourseStatus.PUBLISHED.value)
            .order_by(CourseModel.published_at.desc(), CourseModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_course_view(model) for model in result]

    async def list_by_author(self, *, author_id: UUID, limit: int, offset: int) -> list[CourseView]:
        result = await self._session.scalars(
            select(CourseModel)
            .where(CourseModel.author_id == author_id)
            .order_by(CourseModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_course_view(model) for model in result]

    async def update_course(self, course_id: UUID, **kwargs: object) -> CourseView:
        model = await self._session.get(CourseModel, course_id, with_for_update=True)
        if model is None:
            raise RuntimeError("Course was removed during update")
        published = kwargs.pop("published", False)
        for field, value in kwargs.items():
            setattr(model, field, value)
        if published:
            model.published_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(model)
        return _course_view(model)

    async def add_module(self, **kwargs: object) -> ModuleView:
        model = CourseModuleModel(**kwargs)
        self._session.add(model)
        await self._session.flush()
        return _module_view(model)

    async def list_modules(self, course_id: UUID) -> list[ModuleView]:
        result = await self._session.scalars(
            select(CourseModuleModel)
            .where(CourseModuleModel.course_id == course_id)
            .order_by(CourseModuleModel.position)
        )
        return [_module_view(model) for model in result]

    async def publish_issues(self, course_id: UUID) -> list[str]:
        modules = await self._session.scalar(
            select(CourseModuleModel.id).where(CourseModuleModel.course_id == course_id).limit(1)
        )
        if modules is None:
            return ["Course needs at least one module"]
        lessons = await self._session.scalar(
            select(LessonModel.id)
            .join(CourseModuleModel, LessonModel.module_id == CourseModuleModel.id)
            .where(CourseModuleModel.course_id == course_id)
            .limit(1)
        )
        if lessons is None:
            return ["Course needs at least one lesson"]
        tasks = await self._session.scalar(
            select(TaskModel.id)
            .join(LessonModel, TaskModel.lesson_id == LessonModel.id)
            .join(CourseModuleModel, LessonModel.module_id == CourseModuleModel.id)
            .where(CourseModuleModel.course_id == course_id)
            .limit(1)
        )
        return [] if tasks is not None else ["Course needs at least one task"]
