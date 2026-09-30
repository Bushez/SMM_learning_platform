from collections.abc import AsyncIterator
from datetime import timedelta

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.auth import AuthService
from app.application.auth.dto import UserView
from app.application.common.errors import AuthenticationError, AuthorizationError
from app.domain.users import Role
from app.infrastructure.config import Settings
from app.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyRefreshSessionRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.persistence.sqlalchemy.transaction import SqlAlchemyTransaction
from app.infrastructure.security import (
    Argon2PasswordHasher,
    JwtAccessTokenIssuer,
    SecureRefreshTokenManager,
)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(
        request.app.state.resources.database, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


def get_auth_service(
    request: Request, session: AsyncSession = Depends(get_db_session)
) -> AuthService:
    settings: Settings = request.app.state.settings
    return AuthService(
        users=SqlAlchemyUserRepository(session),
        sessions=SqlAlchemyRefreshSessionRepository(session),
        passwords=Argon2PasswordHasher(),
        access_tokens=JwtAccessTokenIssuer(
            secret=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
            ttl=timedelta(minutes=settings.access_token_ttl_minutes),
        ),
        refresh_tokens=SecureRefreshTokenManager(settings.jwt_secret),
        transaction=SqlAlchemyTransaction(session),
        refresh_ttl=timedelta(days=settings.refresh_token_ttl_days),
        access_ttl_seconds=settings.access_token_ttl_minutes * 60,
    )


async def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    service: AuthService = Depends(get_auth_service),
) -> UserView:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Authentication is required")
    return await service.current_user(credentials.credentials)


async def require_teacher(
    user: UserView = Depends(require_authenticated_user),
) -> UserView:
    if user.role != Role.TEACHER:
        raise AuthorizationError("Teacher role is required")
    return user
