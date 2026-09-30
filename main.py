"""Compatibility entry point for IDE run configurations.

The application package lives under ``backend``. New commands should use
``uv run --package visual-learning-backend uvicorn app.main:app`` from there.
"""

from backend.app.main import app

__all__ = ["app"]
