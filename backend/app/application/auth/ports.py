from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.users import Role, User


class UserRepository(Protocol):
    async def get_by_normalized_email(self, normalized_email: str) -> User | None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_password_hash(self, user_id: UUID) -> str | None: ...

    async def add(
        self,
        *,
        email: str,
        normalized_email: str,
        password_hash: str,
        display_name: str,
        timezone: str,
        preferred_locale: str,
    ) -> User: ...

    async def change_role(self, user_id: UUID, role: Role) -> User: ...


class RefreshSessionRepository(Protocol):
    async def create(self, *, user_id: UUID, token_hash: str, expires_at: datetime) -> None: ...

    async def rotate(
        self, *, token_hash: str, replacement_hash: str, replacement_expires_at: datetime
    ) -> UUID | None: ...

    async def revoke(self, *, token_hash: str) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...


class AccessTokenIssuer(Protocol):
    def issue(self, *, user_id: UUID, role: Role) -> str: ...

    def subject(self, token: str) -> UUID: ...


class RefreshTokenManager(Protocol):
    def generate(self) -> str: ...

    def hash(self, token: str) -> str: ...


class TransactionManager(Protocol):
    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
