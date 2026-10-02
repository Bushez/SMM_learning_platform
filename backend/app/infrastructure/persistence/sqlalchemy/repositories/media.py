from uuid import UUID

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.media.dto import MediaAssetView
from app.domain.courses import CourseStatus

from ..models.courses import (
    CourseEnrollmentModel,
    CourseModel,
    CourseModuleModel,
    LessonModel,
    TaskModel,
    TaskOptionModel,
)
from ..models.media import MediaAssetModel


def _view(model: MediaAssetModel) -> MediaAssetView:
    return MediaAssetView(
        id=model.id,
        owner_id=model.owner_id,
        object_key=model.object_key,
        content_type=model.content_type,
        size_bytes=model.size_bytes,
        width=model.width,
        height=model.height,
        created_at=model.created_at,
    )


class SqlAlchemyMediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        owner_id: UUID,
        object_key: str,
        content_type: str,
        size_bytes: int,
        width: int,
        height: int,
    ) -> MediaAssetView:
        model = MediaAssetModel(
            owner_id=owner_id,
            object_key=object_key,
            content_type=content_type,
            size_bytes=size_bytes,
            width=width,
            height=height,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _view(model)

    async def get(self, media_id: UUID) -> MediaAssetView | None:
        model = await self._session.get(MediaAssetModel, media_id)
        return None if model is None else _view(model)

    async def is_owned_by(self, *, media_id: UUID, owner_id: UUID) -> bool:
        found = await self._session.scalar(
            select(MediaAssetModel.id).where(
                MediaAssetModel.id == media_id, MediaAssetModel.owner_id == owner_id
            )
        )
        return found is not None

    async def can_download(self, *, media_id: UUID, requester_id: UUID) -> bool:
        asset = await self._session.get(MediaAssetModel, media_id)
        if asset is None:
            return False
        if asset.owner_id == requester_id:
            return True

        published_statuses = [CourseStatus.PUBLISHED.value, CourseStatus.ARCHIVED.value]
        public_cover = exists(
            select(CourseModel.id).where(
                CourseModel.cover_media_id == media_id,
                CourseModel.status.in_(published_statuses),
            )
        )
        enrolled_task_media = exists(
            select(TaskModel.id)
            .join(LessonModel, TaskModel.lesson_id == LessonModel.id)
            .join(CourseModuleModel, LessonModel.module_id == CourseModuleModel.id)
            .join(CourseModel, CourseModuleModel.course_id == CourseModel.id)
            .join(
                CourseEnrollmentModel,
                and_(
                    CourseEnrollmentModel.course_id == CourseModel.id,
                    CourseEnrollmentModel.user_id == requester_id,
                ),
            )
            .outerjoin(TaskOptionModel, TaskOptionModel.task_id == TaskModel.id)
            .where(
                CourseModel.status.in_(published_statuses),
                or_(
                    TaskModel.prompt_media_id == media_id,
                    TaskModel.result_media_id == media_id,
                    TaskOptionModel.media_id == media_id,
                ),
            )
        )
        return bool(await self._session.scalar(select(or_(public_cover, enrolled_task_media))))
