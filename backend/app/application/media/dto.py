from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MediaAssetView:
    id: UUID
    owner_id: UUID
    object_key: str
    content_type: str
    size_bytes: int
    width: int
    height: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ImageInspection:
    content_type: str
    extension: str
    width: int
    height: int
