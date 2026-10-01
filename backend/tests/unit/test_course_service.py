from uuid import uuid4

import pytest

from app.application.common.errors import AuthorizationError, ConflictError
from app.application.courses.dto import CourseView
from app.application.courses.service import CourseService
from app.domain.courses import CourseStatus


class FakeCourses:
    def __init__(self) -> None:
        self.course = CourseView(
            id=uuid4(),
            author_id=uuid4(),
            title="Draft",
            slug="draft",
            description="Description",
            cover_media_id=None,
            category="Photography",
            language_code="ru",
            status=CourseStatus.DRAFT,
        )
        self.issues: list[str] = []

    async def create_course(self, **_: object) -> CourseView:
        return self.course

    async def get_course(self, _: object) -> CourseView:
        return self.course

    async def get_by_slug(self, _: object) -> CourseView:
        return self.course

    async def list_published(self, **_: object) -> list[CourseView]:
        return []

    async def list_by_author(self, **_: object) -> list[CourseView]:
        return [self.course]

    async def update_course(self, _: object, **kwargs: object) -> CourseView:
        status = CourseStatus(str(kwargs.get("status", self.course.status)))
        self.course = CourseView(
            id=self.course.id,
            author_id=self.course.author_id,
            title=self.course.title,
            slug=self.course.slug,
            description=self.course.description,
            cover_media_id=self.course.cover_media_id,
            category=self.course.category,
            language_code=self.course.language_code,
            status=status,
        )
        return self.course

    async def publish_issues(self, _: object) -> list[str]:
        return self.issues


class FakeTransaction:
    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


class FakeMedia:
    async def is_owned_by(self, **_: object) -> bool:
        return True


def make_service(courses: FakeCourses) -> CourseService:
    return CourseService(courses=courses, media=FakeMedia(), transaction=FakeTransaction())


@pytest.mark.asyncio
async def test_only_owner_can_publish_course() -> None:
    courses = FakeCourses()
    with pytest.raises(AuthorizationError):
        await make_service(courses).publish(author_id=uuid4(), course_id=courses.course.id)


@pytest.mark.asyncio
async def test_publish_returns_validation_errors_before_status_change() -> None:
    courses = FakeCourses()
    courses.issues = ["Course needs at least one task"]
    with pytest.raises(ConflictError, match="at least one task"):
        await make_service(courses).publish(
            author_id=courses.course.author_id, course_id=courses.course.id
        )
    assert courses.course.status == CourseStatus.DRAFT
