import pytest
from pydantic import ValidationError

from app.infrastructure.config import Settings


def test_production_rejects_development_secrets() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production")
