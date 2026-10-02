from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.application.auth.dto import UserView
from app.application.common.errors import ValidationError
from app.application.media import MediaService
from app.application.media.dto import MediaAssetView
from app.presentation.api.dependencies import (
    get_media_service,
    require_authenticated_user,
    require_teacher,
)

router = APIRouter(prefix="/media", tags=["Media"])


class MediaAssetResponse(BaseModel):
    id: UUID
    content_type: str
    size_bytes: int
    width: int
    height: int

    @classmethod
    def from_view(cls, media: MediaAssetView) -> "MediaAssetResponse":
        return cls(
            id=media.id,
            content_type=media.content_type,
            size_bytes=media.size_bytes,
            width=media.width,
            height=media.height,
        )


@router.post(
    "/images",
    response_model=MediaAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image for teacher-owned course content",
    operation_id="uploadImage",
)
async def upload_image(
    request: Request,
    file: UploadFile = File(description="JPEG, PNG, or WebP image"),
    teacher: UserView = Depends(require_teacher),
    service: MediaService = Depends(get_media_service),
) -> MediaAssetResponse:
    max_size = request.app.state.settings.max_upload_size_bytes
    content = await file.read(max_size + 1)
    if len(content) > max_size:
        raise ValidationError("Image exceeds the configured upload size limit")
    media = await service.upload_image(
        owner_id=teacher.id,
        content=content,
        declared_content_type=file.content_type,
        filename=file.filename,
    )
    return MediaAssetResponse.from_view(media)


@router.get(
    "/{media_id}/download",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Get a temporary download URL for accessible course media",
    operation_id="downloadMedia",
)
async def download_owned_media(
    media_id: UUID,
    user: UserView = Depends(require_authenticated_user),
    service: MediaService = Depends(get_media_service),
) -> RedirectResponse:
    url = await service.get_download_url(requester_id=user.id, media_id=media_id)
    return RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
