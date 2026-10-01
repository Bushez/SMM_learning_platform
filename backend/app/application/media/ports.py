from typing import Protocol
from uuid import UUID

from .dto import ImageInspection, MediaAssetView


class MediaRepository(Protocol):
    async def add(
        self,
        *,
        owner_id: UUID,
        object_key: str,
        content_type: str,
        size_bytes: int,
        width: int,
        height: int,
    ) -> MediaAssetView: ...

    async def get(self, media_id: UUID) -> MediaAssetView | None: ...

    async def is_owned_by(self, *, media_id: UUID, owner_id: UUID) -> bool: ...


class StoragePort(Protocol):
    async def put_image(self, *, object_key: str, content: bytes, content_type: str) -> None: ...

    async def delete(self, *, object_key: str) -> None: ...

    async def get_download_url(self, *, object_key: str) -> str: ...


class ImageInspector(Protocol):
    def inspect(
        self, *, content: bytes, declared_content_type: str | None, filename: str | None
    ) -> ImageInspection: ...


class MediaTransaction(Protocol):
    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
