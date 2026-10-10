from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PhotoAdjustments:
    exposure: float = 0
    temperature: int = 0
    tint: int = 0
    contrast: int = 0
    highlights: int = 0
    shadows: int = 0
    saturation: int = 0
    aperture: float = 8
    shutter_speed: float = 1 / 125
    iso: int = 100


@dataclass(frozen=True, slots=True)
class PhotoPreset:
    id: UUID
    title: str
    author_name: str
    description: str
    adjustments: PhotoAdjustments
