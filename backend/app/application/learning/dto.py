from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LessonProgressView:
    id: UUID
    module_id: UUID
    title: str
    position: int
    total_tasks: int
    completed_tasks: int
    completed: bool
    unlocked: bool


@dataclass(frozen=True, slots=True)
class ModuleProgressView:
    id: UUID
    title: str
    position: int
    lessons: tuple[LessonProgressView, ...]
    completed: bool


@dataclass(frozen=True, slots=True)
class CourseProgressView:
    course_id: UUID
    enrolled: bool
    total_tasks: int
    completed_tasks: int
    progress_percent: int
    completed: bool
    modules: tuple[ModuleProgressView, ...] = ()


@dataclass(frozen=True, slots=True)
class CompletionUpdate:
    course_id: UUID
    first_task_completion: bool
    lesson_completed: bool
    module_completed: bool
    course_completed: bool
    course_progress_percent: int
