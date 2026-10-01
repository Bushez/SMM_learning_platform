from io import BytesIO
from uuid import uuid4

import pytest
from PIL import Image

from app.application.common.errors import ValidationError
from app.application.media.dto import MediaAssetView
from app.application.media.service import MediaService
from app.infrastructure.storage import MinioStorage, PillowImageInspector


def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (4, 3), "white").save(output, format="PNG")
    return output.getvalue()


class FakeStorage:
    def __init__(self) -> None:
        self.put_keys: list[str] = []
        self.deleted_keys: list[str] = []

    async def put_image(self, *, object_key: str, **_: object) -> None:
        self.put_keys.append(object_key)

    async def delete(self, *, object_key: str) -> None:
        self.deleted_keys.append(object_key)

    async def get_download_url(self, **_: object) -> str:
        return "https://storage.example/image"


class FailingMediaRepository:
    async def add(self, **_: object) -> MediaAssetView:
        raise RuntimeError("database error")

    async def get(self, **_: object) -> MediaAssetView | None:
        return None

    async def is_owned_by(self, **_: object) -> bool:
        return False


class FakeTransaction:
    def __init__(self) -> None:
        self.rolled_back = False

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        self.rolled_back = True


def test_image_inspector_rejects_mismatched_content_type() -> None:
    inspector = PillowImageInspector(max_size_bytes=1024)
    with pytest.raises(ValidationError, match="MIME"):
        inspector.inspect(
            content=png_bytes(), declared_content_type="image/jpeg", filename="image.png"
        )


def test_image_inspector_reads_real_image_dimensions() -> None:
    inspection = PillowImageInspector(max_size_bytes=1024).inspect(
        content=png_bytes(), declared_content_type="image/png", filename="image.png"
    )
    assert (inspection.content_type, inspection.extension, inspection.width, inspection.height) == (
        "image/png",
        "png",
        4,
        3,
    )


@pytest.mark.asyncio
async def test_upload_deletes_object_when_metadata_persistence_fails() -> None:
    storage = FakeStorage()
    transaction = FakeTransaction()
    service = MediaService(
        media=FailingMediaRepository(),
        storage=storage,
        inspector=PillowImageInspector(max_size_bytes=1024),
        transaction=transaction,
    )

    with pytest.raises(RuntimeError, match="database error"):
        await service.upload_image(
            owner_id=uuid4(),
            content=png_bytes(),
            declared_content_type="image/png",
            filename="image.png",
        )

    assert storage.put_keys == storage.deleted_keys
    assert transaction.rolled_back is True


@pytest.mark.asyncio
async def test_signed_url_uses_public_endpoint_without_a_network_region_lookup() -> None:
    storage = MinioStorage(
        endpoint="minio:9000",
        public_endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        bucket="visual-learning-media",
        secure=False,
        region="us-east-1",
    )

    url = await storage.get_download_url(object_key="images/example.png")

    assert url.startswith("http://localhost:9000/visual-learning-media/images/example.png?")
