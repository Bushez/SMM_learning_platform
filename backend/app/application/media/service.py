from uuid import UUID, uuid4

from app.application.common.errors import NotFoundError

from .dto import MediaAssetView
from .ports import ImageInspector, MediaRepository, MediaTransaction, StoragePort


class MediaService:
    def __init__(
        self,
        *,
        media: MediaRepository,
        storage: StoragePort,
        inspector: ImageInspector,
        transaction: MediaTransaction,
    ) -> None:
        self._media = media
        self._storage = storage
        self._inspector = inspector
        self._transaction = transaction

    async def upload_image(
        self,
        *,
        owner_id: UUID,
        content: bytes,
        declared_content_type: str | None,
        filename: str | None,
    ) -> MediaAssetView:
        inspection = self._inspector.inspect(
            content=content,
            declared_content_type=declared_content_type,
            filename=filename,
        )
        object_key = f"images/{uuid4()}.{inspection.extension}"
        await self._storage.put_image(
            object_key=object_key, content=content, content_type=inspection.content_type
        )
        try:
            asset = await self._media.add(
                owner_id=owner_id,
                object_key=object_key,
                content_type=inspection.content_type,
                size_bytes=len(content),
                width=inspection.width,
                height=inspection.height,
            )
            await self._transaction.commit()
        except Exception:
            await self._transaction.rollback()
            await self._storage.delete(object_key=object_key)
            raise
        return asset

    async def get_download_url(self, *, requester_id: UUID, media_id: UUID) -> str:
        asset = await self._media.get(media_id)
        if asset is None or not await self._media.can_download(
            media_id=media_id, requester_id=requester_id
        ):
            raise NotFoundError("Media asset not found")
        return await self._storage.get_download_url(object_key=asset.object_key)
