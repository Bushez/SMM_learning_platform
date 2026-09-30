import argparse
import asyncio
from datetime import timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.auth import AuthService
from app.infrastructure.config import get_settings
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


async def promote(email: str) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            service = AuthService(
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
            user = await service.promote_teacher(email)
            print(f"Promoted {user.email} to {user.role.value}")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote an existing user to TEACHER")
    parser.add_argument("email")
    args = parser.parse_args()
    asyncio.run(promote(args.email))


if __name__ == "__main__":
    main()
