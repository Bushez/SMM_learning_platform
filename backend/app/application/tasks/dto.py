from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.courses import TaskType


@dataclass(frozen=True, slots=True)
class TaskOptionEditorView:
    id: UUID
    text: str | None
    media_id: UUID | None
    position: int
    is_correct: bool
    feedback_text: str | None
    feedback_media_id: UUID | None


@dataclass(frozen=True, slots=True)
class TeacherTaskView:
    id: UUID
    lesson_id: UUID
    task_type: TaskType
    position: int
    prompt: str
    prompt_media_id: UUID | None
    answer_feedback_text: str | None
    answer_feedback_media_id: UUID | None
    options: tuple[TaskOptionEditorView, ...]
    accepted_answers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LearnerTaskOptionView:
    id: UUID
    text: str | None
    media_id: UUID | None
    position: int


@dataclass(frozen=True, slots=True)
class LearnerTaskView:
    id: UUID
    lesson_id: UUID
    task_type: TaskType
    position: int
    prompt: str
    prompt_media_id: UUID | None
    options: tuple[LearnerTaskOptionView, ...]


@dataclass(frozen=True, slots=True)
class EvaluationTaskView:
    id: UUID
    lesson_id: UUID
    task_type: TaskType
    option_ids: tuple[UUID, ...]
    correct_option_ids: tuple[UUID, ...]
    accepted_answers: tuple[str, ...]
    option_feedback: tuple["OptionFeedback", ...]
    answer_feedback: "OptionFeedback | None"


@dataclass(frozen=True, slots=True)
class OptionFeedback:
    option_id: UUID
    text: str | None
    media_id: UUID | None


@dataclass(frozen=True, slots=True)
class AttemptFeedback:
    attempt_id: UUID
    correct: bool
    correct_option_ids: tuple[UUID, ...]
    created_at: datetime
    option_feedback: tuple[OptionFeedback, ...] = ()
    answer_feedback: OptionFeedback | None = None
    first_task_completion: bool = False
    task_completed: bool = False
    lesson_completed: bool = False
    module_completed: bool = False
    course_completed: bool = False
    course_progress_percent: int | None = None
    xp_awarded: int = 0
    current_streak: int | None = None
    longest_streak: int | None = None
