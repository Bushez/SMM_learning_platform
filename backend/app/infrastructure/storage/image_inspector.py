from io import BytesIO
from pathlib import Path
from typing import ClassVar

from PIL import Image, UnidentifiedImageError

from app.application.common.errors import ValidationError
from app.application.media.dto import ImageInspection


class PillowImageInspector:
    _formats: ClassVar[dict[str, tuple[str, str]]] = {
        "JPEG": ("image/jpeg", "jpg"),
        "PNG": ("image/png", "png"),
        "WEBP": ("image/webp", "webp"),
    }

    def __init__(self, *, max_size_bytes: int) -> None:
        self._max_size_bytes = max_size_bytes

    def inspect(
        self, *, content: bytes, declared_content_type: str | None, filename: str | None
    ) -> ImageInspection:
        if not content:
            raise ValidationError("Image file is empty")
        if len(content) > self._max_size_bytes:
            raise ValidationError("Image exceeds the configured upload size limit")
        try:
            with Image.open(BytesIO(content)) as image:
                image.verify()
            with Image.open(BytesIO(content)) as image:
                image.load()
                format_name = image.format
                width, height = image.size
        except (UnidentifiedImageError, OSError, ValueError) as error:
            raise ValidationError("Uploaded file is not a valid image") from error
        if format_name not in self._formats:
            raise ValidationError("Only JPEG, PNG, and WebP images are allowed")
        content_type, extension = self._formats[format_name]
        if declared_content_type is not None and declared_content_type.lower() != content_type:
            raise ValidationError("Image MIME type does not match its content")
        if filename:
            suffix = Path(filename).suffix.lower().lstrip(".")
            allowed_suffixes = {extension, "jpeg" if extension == "jpg" else extension}
            if suffix not in allowed_suffixes:
                raise ValidationError("Image extension does not match its content")
        return ImageInspection(
            content_type=content_type, extension=extension, width=width, height=height
        )
