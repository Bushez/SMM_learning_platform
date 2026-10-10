from collections.abc import AsyncIterator
from datetime import timedelta

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.auth import AuthService
from app.application.auth.dto import UserView
from app.application.common.errors import AuthenticationError, AuthorizationError
from app.application.courses import CourseService
from app.application.gamification import GamificationService
from app.application.learning import LearningService
from app.application.media import MediaService
from app.application.tasks import TaskService
from app.domain.users import Role
from app.infrastructure.config import Settings
from app.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyCourseRepository,
    SqlAlchemyGamificationRepository,
    SqlAlchemyLearningRepository,
    SqlAlchemyMediaRepository,
    SqlAlchemyRefreshSessionRepository,
    SqlAlchemyTaskRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.persistence.sqlalchemy.transaction import SqlAlchemyTransaction
from app.infrastructure.security import (
    Argon2PasswordHasher,
    JwtAccessTokenIssuer,
    SecureRefreshTokenManager,
)
from app.infrastructure.storage import MinioStorage, PillowImageInspector

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


def get_course_service(session: AsyncSession = Depends(get_db_session)) -> CourseService:
    return CourseService(
        courses=SqlAlchemyCourseRepository(session),
        media=SqlAlchemyMediaRepository(session),
        transaction=SqlAlchemyTransaction(session),
    )


def get_media_service(
    request: Request, session: AsyncSession = Depends(get_db_session)
) -> MediaService:
    settings: Settings = request.app.state.settings
    return MediaService(
        media=SqlAlchemyMediaRepository(session),
        storage=MinioStorage(
            endpoint=settings.minio_endpoint,
            public_endpoint=settings.minio_public_endpoint,
            region=settings.minio_region,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
            secure=settings.minio_secure,
            public_secure=settings.minio_public_secure,
        ),
        inspector=PillowImageInspector(max_size_bytes=settings.max_upload_size_bytes),
        transaction=SqlAlchemyTransaction(session),
    )


def get_task_service(
    request: Request, session: AsyncSession = Depends(get_db_session)
) -> TaskService:
    settings: Settings = request.app.state.settings
    return TaskService(
        tasks=SqlAlchemyTaskRepository(session),
        media=SqlAlchemyMediaRepository(session),
        learning=SqlAlchemyLearningRepository(session),
        gamification=GamificationService(
            gamification=SqlAlchemyGamificationRepository(session),
            task_completion_xp=settings.task_completion_xp,
        ),
        transaction=SqlAlchemyTransaction(session),
    )


def get_gamification_service(
    request: Request, session: AsyncSession = Depends(get_db_session)
) -> GamificationService:
    settings: Settings = request.app.state.settings
    return GamificationService(
        gamification=SqlAlchemyGamificationRepository(session),
        task_completion_xp=settings.task_completion_xp,
    )


def get_learning_service(session: AsyncSession = Depends(get_db_session)) -> LearningService:
    return LearningService(
        learning=SqlAlchemyLearningRepository(session),
        transaction=SqlAlchemyTransaction(session),
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
