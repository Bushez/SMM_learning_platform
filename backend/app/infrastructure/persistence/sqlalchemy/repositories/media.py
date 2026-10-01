from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.media.dto import MediaAssetView

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
