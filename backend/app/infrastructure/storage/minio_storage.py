import asyncio
from datetime import timedelta
from io import BytesIO

from minio import Minio


class MinioStorage:
    def __init__(
        self,
        *,
        endpoint: str,
        public_endpoint: str,
        region: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
        public_secure: bool = False,
    ) -> None:
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )
        self._public_client = Minio(
            public_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=public_secure,
            region=region,
        )
        self._bucket = bucket

    async def put_image(self, *, object_key: str, content: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            self._bucket,
            object_key,
            BytesIO(content),
            len(content),
            content_type=content_type,
        )

    async def delete(self, *, object_key: str) -> None:
        await asyncio.to_thread(self._client.remove_object, self._bucket, object_key)

    async def get_download_url(self, *, object_key: str) -> str:
        return await asyncio.to_thread(
            self._public_client.presigned_get_object,
            self._bucket,
            object_key,
            expires=timedelta(minutes=15),
        )
