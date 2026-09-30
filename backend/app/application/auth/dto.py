from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.users import Role


@dataclass(frozen=True, slots=True)
class UserView:
    id: UUID
    email: str
    display_name: str
    role: Role
    timezone: str
    preferred_locale: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    access_token: str
    access_token_expires_in: int
    refresh_token: str
    user: UserView
