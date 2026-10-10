from fastapi import APIRouter
from pydantic import BaseModel

from app.application.photo_lab import PhotoLabService
from app.domain.photo_lab import PhotoAdjustments, PhotoPreset

router = APIRouter(prefix="/photo-lab", tags=["Photo Lab"])


class PhotoAdjustmentsResponse(BaseModel):
    exposure: float
    temperature: int
    tint: int
    contrast: int
    highlights: int
    shadows: int
    saturation: int
    aperture: float
    shutter_speed: float
    iso: int

    @classmethod
    def from_domain(cls, value: PhotoAdjustments) -> "PhotoAdjustmentsResponse":
        return cls(**{field: getattr(value, field) for field in cls.model_fields})


class PhotoPresetResponse(BaseModel):
    id: str
    title: str
    author_name: str
    description: str
    adjustments: PhotoAdjustmentsResponse

    @classmethod
    def from_domain(cls, value: PhotoPreset) -> "PhotoPresetResponse":
        return cls(
            id=str(value.id),
            title=value.title,
            author_name=value.author_name,
            description=value.description,
            adjustments=PhotoAdjustmentsResponse.from_domain(value.adjustments),
        )


@router.get(
    "/presets",
    response_model=list[PhotoPresetResponse],
    summary="List curated master presets",
    operation_id="listPhotoLabPresets",
)
async def list_presets() -> list[PhotoPresetResponse]:
    return [
        PhotoPresetResponse.from_domain(item) for item in PhotoLabService().list_master_presets()
    ]
