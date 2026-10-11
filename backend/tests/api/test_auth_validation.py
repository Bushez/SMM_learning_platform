import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.application.common.errors import ConflictError
from app.infrastructure.config import Settings
from app.main import create_app
from app.presentation.api.v1.auth import logout


def test_register_validation_error_uses_the_standard_error_contract() -> None:
    application = create_app(Settings(app_env="test"))
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "short",
                "display_name": "A",
                "timezone": "Unknown/Timezone",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["trace_id"]
    assert isinstance(body["error"]["details"], list)


def test_media_upload_requires_teacher_authentication() -> None:
    application = create_app(Settings(app_env="test"))
    with TestClient(application) as client:
        response = client.post(
            "/api/v1/media/images",
            files={"file": ("image.png", b"not-an-image", "image/png")},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_failed"


def test_application_error_preserves_structured_details() -> None:
    application = create_app(Settings(app_env="test"))

    @application.get("/test-conflict")
    async def raise_conflict() -> None:
        raise ConflictError(
            "Course cannot be published", details=["Course needs at least one module"]
        )

    with TestClient(application) as client:
        response = client.get("/test-conflict")

    assert response.status_code == 409
    assert response.json()["error"]["details"] == ["Course needs at least one module"]


class FakeAuthService:
    def __init__(self) -> None:
        self.revoked_token: str | None = None

    async def logout(self, refresh_token: str | None) -> None:
        self.revoked_token = refresh_token


@pytest.mark.asyncio
async def test_logout_returns_204_and_clears_refresh_cookie() -> None:
    application = create_app(Settings(app_env="test"))
    request = Request(
        {
            "type": "http",
            "app": application,
            "headers": [(b"cookie", b"vl_refresh=refresh-token")],
        }
    )
    service = FakeAuthService()

    response = await logout(request=request, service=service)

    assert response.status_code == 204
    assert service.revoked_token == "refresh-token"
    assert 'vl_refresh=""' in response.headers["set-cookie"]
