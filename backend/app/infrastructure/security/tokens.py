import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.application.common.errors import AuthenticationError
from app.domain.users import Role


class JwtAccessTokenIssuer:
    def __init__(self, *, secret: str, algorithm: str, ttl: timedelta) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._ttl = ttl

    def issue(self, *, user_id: UUID, role: Role) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {"sub": str(user_id), "role": role.value, "iat": now, "exp": now + self._ttl},
            self._secret,
            algorithm=self._algorithm,
        )

    def subject(self, token: str) -> UUID:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            return UUID(str(payload["sub"]))
        except (jwt.InvalidTokenError, KeyError, ValueError) as error:
            raise AuthenticationError("Access token is invalid or expired") from error


class SecureRefreshTokenManager:
    def __init__(self, secret: str) -> None:
        self._secret = secret.encode()

    def generate(self) -> str:
        return secrets.token_urlsafe(48)

    def hash(self, token: str) -> str:
        return hmac.new(self._secret, token.encode(), hashlib.sha256).hexdigest()
