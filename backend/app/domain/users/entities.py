from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    USER = "USER"
    TEACHER = "TEACHER"


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    normalized_email: str
    display_name: str
    role: Role
    timezone: str
    preferred_locale: str
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
