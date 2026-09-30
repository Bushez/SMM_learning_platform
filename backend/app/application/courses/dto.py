from dataclasses import dataclass
from uuid import UUID

from app.domain.courses import CourseStatus


@dataclass(frozen=True, slots=True)
class CourseView:
    id: UUID
    author_id: UUID
    title: str
    slug: str
    description: str
    category: str
    language_code: str
    status: CourseStatus


@dataclass(frozen=True, slots=True)
class ModuleView:
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    position: int
