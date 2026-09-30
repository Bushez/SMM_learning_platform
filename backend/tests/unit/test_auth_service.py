from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.application.auth.use_cases import AuthService
from app.application.common.errors import ConflictError
from app.domain.users import Role, User


class FakeUsers:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.passwords: dict[UUID, str] = {}

    async def get_by_normalized_email(self, normalized_email: str) -> User | None:
        return self.users.get(normalized_email)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return next((user for user in self.users.values() if user.id == user_id), None)

    async def get_password_hash(self, user_id: UUID) -> str | None:
        return self.passwords.get(user_id)

    async def add(self, **kwargs: str) -> User:
        now = datetime.now(UTC)
        user = User(
            id=uuid4(),
            email=kwargs["email"],
            normalized_email=kwargs["normalized_email"],
            display_name=kwargs["display_name"],
            role=Role.USER,
            timezone=kwargs["timezone"],
            preferred_locale=kwargs["preferred_locale"],
            email_verified_at=None,
            created_at=now,
            updated_at=now,
        )
        self.users[user.normalized_email] = user
        self.passwords[user.id] = kwargs["password_hash"]
        return user

    async def change_role(self, user_id: UUID, role: Role) -> User:
        user = await self.get_by_id(user_id)
        assert user is not None
        replacement = User(
            id=user.id,
            email=user.email,
            normalized_email=user.normalized_email,
            display_name=user.display_name,
            role=role,
            timezone=user.timezone,
            preferred_locale=user.preferred_locale,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self.users[replacement.normalized_email] = replacement
        return replacement


class FakeSessions:
    async def create(self, **_: object) -> None:
        return None

    async def rotate(self, **_: object) -> UUID | None:
        return None

    async def revoke(self, **_: object) -> None:
        return None


class FakePasswords:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == self.hash(password)


class FakeTokens:
    def issue(self, **_: object) -> str:
        return "access-token"

    def subject(self, _: str) -> UUID:
        raise AssertionError("not used in this test")


class FakeRefreshTokens:
    def generate(self) -> str:
        return "refresh-token"

    def hash(self, token: str) -> str:
        return token


class FakeTransaction:
    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def make_service(users: FakeUsers) -> AuthService:
    return AuthService(
        users=users,
        sessions=FakeSessions(),
        passwords=FakePasswords(),
        access_tokens=FakeTokens(),
        refresh_tokens=FakeRefreshTokens(),
        transaction=FakeTransaction(),
        refresh_ttl=timedelta(days=30),
        access_ttl_seconds=900,
    )


@pytest.mark.asyncio
async def test_register_normalizes_email_and_assigns_user_role() -> None:
    users = FakeUsers()
    result = await make_service(users).register(
        email="  Example@Email.Test ",
        password="password-value",
        display_name=" Visual learner ",
        timezone="Europe/Moscow",
        preferred_locale="ru",
    )

    assert result.email == "Example@Email.Test"
    assert result.role == Role.USER
    assert "example@email.test" in users.users


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email_case_insensitively() -> None:
    users = FakeUsers()
    service = make_service(users)
    await service.register(
        email="learner@example.test",
        password="password-value",
        display_name="Learner",
        timezone="Europe/Moscow",
        preferred_locale="ru",
    )

    with pytest.raises(ConflictError):
        await service.register(
            email="LEARNER@example.test",
            password="another-password",
            display_name="Other",
            timezone="Europe/Moscow",
            preferred_locale="ru",
        )
