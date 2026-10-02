from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.users import Role, User

from ..models import RefreshSessionModel, UserModel


def _to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        normalized_email=model.normalized_email,
        display_name=model.display_name,
        role=Role(model.role),
        timezone=model.timezone,
        preferred_locale=model.preferred_locale,
        email_verified_at=model.email_verified_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_normalized_email(self, normalized_email: str) -> User | None:
        model = await self._session.scalar(
            select(UserModel).where(UserModel.normalized_email == normalized_email)
        )
        return None if model is None else _to_domain(model)

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return None if model is None else _to_domain(model)

    async def get_password_hash(self, user_id: UUID) -> str | None:
        password_hash = await self._session.scalar(
            select(UserModel.password_hash).where(UserModel.id == user_id)
        )
        return password_hash

    async def add(
        self,
        *,
        email: str,
        normalized_email: str,
        password_hash: str,
        display_name: str,
        timezone: str,
        preferred_locale: str,
    ) -> User:
        model = UserModel(
            email=email,
            normalized_email=normalized_email,
            password_hash=password_hash,
            display_name=display_name,
            timezone=timezone,
            preferred_locale=preferred_locale,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_domain(model)

    async def change_role(self, user_id: UUID, role: Role) -> User:
        model = await self._session.get(UserModel, user_id, with_for_update=True)
        if model is None:
            raise RuntimeError("User was removed during role update")
        model.role = role.value
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)


class SqlAlchemyRefreshSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._session.add(
            RefreshSessionModel(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        )
        await self._session.flush()

    async def rotate(
        self, *, token_hash: str, replacement_hash: str, replacement_expires_at: datetime
    ) -> UUID | None:
        current = await self._session.scalar(
            select(RefreshSessionModel)
            .where(RefreshSessionModel.token_hash == token_hash)
            .with_for_update()
        )
        now = datetime.now(UTC)
        if current is None or current.revoked_at is not None or current.expires_at <= now:
            return None
        replacement = RefreshSessionModel(
            user_id=current.user_id,
            token_hash=replacement_hash,
            expires_at=replacement_expires_at,
        )
        self._session.add(replacement)
        await self._session.flush()
        current.revoked_at = now
        current.replaced_by_id = replacement.id
        return current.user_id

    async def revoke(self, *, token_hash: str) -> None:
        current = await self._session.scalar(
            select(RefreshSessionModel)
            .where(RefreshSessionModel.token_hash == token_hash)
            .with_for_update()
        )
        if current is not None and current.revoked_at is None:
            current.revoked_at = datetime.now(UTC)
