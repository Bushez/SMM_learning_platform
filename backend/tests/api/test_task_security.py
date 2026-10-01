from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.application.auth.dto import UserView
from app.application.tasks.dto import LearnerTaskOptionView, LearnerTaskView
from app.domain.courses import TaskType
from app.domain.users import Role
from app.infrastructure.config import Settings
from app.main import create_app
from app.presentation.api.dependencies import get_task_service, require_authenticated_user


class FakeTaskService:
    async def learner_tasks(self, *, user_id: UUID, lesson_id: UUID) -> list[LearnerTaskView]:
        return [
            LearnerTaskView(
                id=uuid4(),
                lesson_id=lesson_id,
                task_type=TaskType.SINGLE_CHOICE,
                position=1,
                prompt="Choose the correct answer",
                prompt_media_id=None,
                options=(
                    LearnerTaskOptionView(id=uuid4(), text="Option", media_id=None, position=1),
                ),
            )
        ]


async def fake_user() -> UserView:
    return UserView(
        id=uuid4(),
        email="learner@example.test",
        display_name="Learner",
        role=Role.USER,
        timezone="Europe/Moscow",
        preferred_locale="ru",
        created_at=datetime.now(UTC),
    )


def test_learner_task_response_never_leaks_correctness_data() -> None:
    application = create_app(Settings(app_env="test"))
    application.dependency_overrides[get_task_service] = lambda: FakeTaskService()
    application.dependency_overrides[require_authenticated_user] = fake_user
    try:
        with TestClient(application) as client:
            response = client.get(f"/api/v1/learning/lessons/{uuid4()}/tasks")
    finally:
        application.dependency_overrides.clear()

    assert response.status_code == 200
    serialized = response.text
    assert "is_correct" not in serialized
    assert "correct_option" not in serialized
    assert "accepted_answer" not in serialized
    assert "explanation" not in serialized
