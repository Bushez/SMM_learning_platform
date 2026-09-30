from datetime import UTC, datetime, timedelta

from app.application.common.errors import AuthenticationError, ConflictError, NotFoundError
from app.domain.users import Role, User

from .dto import AuthenticatedSession, UserView
from .ports import (
    AccessTokenIssuer,
    PasswordHasher,
    RefreshSessionRepository,
    RefreshTokenManager,
    TransactionManager,
    UserRepository,
)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def to_user_view(user: User) -> UserView:
    return UserView(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        timezone=user.timezone,
        preferred_locale=user.preferred_locale,
        created_at=user.created_at,
    )


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        sessions: RefreshSessionRepository,
        passwords: PasswordHasher,
        access_tokens: AccessTokenIssuer,
        refresh_tokens: RefreshTokenManager,
        transaction: TransactionManager,
        refresh_ttl: timedelta,
        access_ttl_seconds: int,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._passwords = passwords
        self._access_tokens = access_tokens
        self._refresh_tokens = refresh_tokens
        self._transaction = transaction
        self._refresh_ttl = refresh_ttl
        self._access_ttl_seconds = access_ttl_seconds

    async def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str,
        timezone: str,
        preferred_locale: str,
    ) -> UserView:
        normalized_email = normalize_email(email)
        if await self._users.get_by_normalized_email(normalized_email):
            raise ConflictError("An account with this email already exists")
        user = await self._users.add(
            email=email.strip(),
            normalized_email=normalized_email,
            password_hash=self._passwords.hash(password),
            display_name=display_name.strip(),
            timezone=timezone,
            preferred_locale=preferred_locale,
        )
        try:
            await self._transaction.commit()
        except Exception:
            await self._transaction.rollback()
            raise
        return to_user_view(user)

    async def authenticate(self, *, email: str, password: str) -> AuthenticatedSession:
        user = await self._users.get_by_normalized_email(normalize_email(email))
        password_hash = None if user is None else await self._users.get_password_hash(user.id)
        if (
            user is None
            or password_hash is None
            or not self._passwords.verify(password, password_hash)
        ):
            raise AuthenticationError("Invalid email or password")
        return await self._create_session(user)

    async def refresh(self, refresh_token: str) -> AuthenticatedSession:
        new_token = self._refresh_tokens.generate()
        user_id = await self._sessions.rotate(
            token_hash=self._refresh_tokens.hash(refresh_token),
            replacement_hash=self._refresh_tokens.hash(new_token),
            replacement_expires_at=datetime.now(UTC) + self._refresh_ttl,
        )
        if user_id is None:
            raise AuthenticationError("Refresh session is invalid or expired")
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("Refresh session is invalid")
        try:
            await self._transaction.commit()
        except Exception:
            await self._transaction.rollback()
            raise
        return self._session_view(user, new_token)

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token is not None:
            await self._sessions.revoke(token_hash=self._refresh_tokens.hash(refresh_token))
            await self._transaction.commit()

    async def current_user(self, access_token: str) -> UserView:
        user = await self._users.get_by_id(self._access_tokens.subject(access_token))
        if user is None:
            raise NotFoundError("User not found")
        return to_user_view(user)

    async def promote_teacher(self, email: str) -> UserView:
        user = await self._users.get_by_normalized_email(normalize_email(email))
        if user is None:
            raise NotFoundError("User not found")
        if user.role != Role.TEACHER:
            user = await self._users.change_role(user.id, Role.TEACHER)
            await self._transaction.commit()
        return to_user_view(user)

    async def _create_session(self, user: User) -> AuthenticatedSession:
        refresh_token = self._refresh_tokens.generate()
        await self._sessions.create(
            user_id=user.id,
            token_hash=self._refresh_tokens.hash(refresh_token),
            expires_at=datetime.now(UTC) + self._refresh_ttl,
        )
        try:
            await self._transaction.commit()
        except Exception:
            await self._transaction.rollback()
            raise
        return self._session_view(user, refresh_token)

    def _session_view(self, user: User, refresh_token: str) -> AuthenticatedSession:
        return AuthenticatedSession(
            access_token=self._access_tokens.issue(user_id=user.id, role=user.role),
            access_token_expires_in=self._access_ttl_seconds,
            refresh_token=refresh_token,
            user=to_user_view(user),
        )
