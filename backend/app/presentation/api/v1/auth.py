from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.application.auth import AuthService
from app.application.auth.dto import AuthenticatedSession, UserView
from app.domain.users import Role
from app.infrastructure.config import Settings
from app.presentation.api.dependencies import get_auth_service, require_authenticated_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=2, max_length=80)
    timezone: str = Field(default="Europe/Moscow", max_length=64)
    preferred_locale: str = Field(default="ru", min_length=2, max_length=16)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("A valid email address is required")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("A valid IANA timezone is required") from error
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: Role
    timezone: str
    preferred_locale: str

    @classmethod
    def from_view(cls, user: UserView) -> "UserResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            timezone=user.timezone,
            preferred_locale=user.preferred_locale,
        )


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


def _auth_response(session: AuthenticatedSession) -> AuthResponse:
    return AuthResponse(
        access_token=session.access_token,
        expires_in=session.access_token_expires_in,
        user=UserResponse.from_view(session.user),
    )


def _set_refresh_cookie(response: Response, request: Request, token: str) -> None:
    settings: Settings = request.app.state.settings
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
    )


def _clear_refresh_cookie(response: Response, request: Request) -> None:
    settings: Settings = request.app.state.settings
    response.delete_cookie(key=settings.refresh_cookie_name, path=settings.refresh_cookie_path)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a learner account",
    operation_id="registerUser",
)
async def register(
    payload: RegisterRequest, service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    user = await service.register(**payload.model_dump())
    return UserResponse.from_view(user)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate with email and password",
    operation_id="loginUser",
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    session = await service.authenticate(**payload.model_dump())
    _set_refresh_cookie(response, request, session.refresh_token)
    return _auth_response(session)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Rotate refresh session and issue a new access token",
    operation_id="refreshSession",
)
async def refresh(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    settings: Settings = request.app.state.settings
    token = request.cookies.get(settings.refresh_cookie_name)
    if token is None:
        from app.application.common.errors import AuthenticationError

        raise AuthenticationError("Refresh session is missing")
    session = await service.refresh(token)
    _set_refresh_cookie(response, request, session.refresh_token)
    return _auth_response(session)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current refresh session",
    operation_id="logoutUser",
)
async def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    settings: Settings = request.app.state.settings
    await service.logout(request.cookies.get(settings.refresh_cookie_name))
    _clear_refresh_cookie(response, request)
    return response


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user",
    operation_id="getCurrentUser",
)
async def current_user(user: UserView = Depends(require_authenticated_user)) -> UserResponse:
    return UserResponse.from_view(user)
