from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from pydantic import BaseModel, ConfigDict, Field

from app.application.auth.dto import UserView
from app.application.tasks import TaskService
from app.application.tasks.dto import (
    AttemptFeedback,
    LearnerTaskOptionView,
    LearnerTaskView,
    TaskOptionEditorView,
    TeacherTaskView,
)
from app.domain.courses import TaskType
from app.presentation.api.dependencies import (
    get_task_service,
    require_authenticated_user,
    require_teacher,
)

teacher_router = APIRouter(prefix="/teacher", tags=["Teacher"])
learning_router = APIRouter(prefix="/learning", tags=["Learning"])


class TaskOptionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str | None = Field(default=None, max_length=10_000)
    media_id: UUID | None = None
    position: int = Field(ge=1)
    is_correct: bool


class TaskBaseRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    position: int = Field(ge=1)
    prompt: str = Field(min_length=1, max_length=10_000)
    prompt_media_id: UUID | None = None
    explanation: str = Field(min_length=1, max_length=10_000)
    result_media_id: UUID | None = None


class SingleChoiceTaskRequest(TaskBaseRequest):
    task_type: Literal[TaskType.SINGLE_CHOICE]
    options: list[TaskOptionRequest] = Field(min_length=2)
    accepted_answers: list[str] = Field(default_factory=list)


class MultipleChoiceTaskRequest(TaskBaseRequest):
    task_type: Literal[TaskType.MULTIPLE_CHOICE]
    options: list[TaskOptionRequest] = Field(min_length=2)
    accepted_answers: list[str] = Field(default_factory=list)


class TextInputTaskRequest(TaskBaseRequest):
    task_type: Literal[TaskType.TEXT_INPUT]
    options: list[TaskOptionRequest] = Field(default_factory=list)
    accepted_answers: list[str] = Field(min_length=1)


CreateTaskRequest = Annotated[
    SingleChoiceTaskRequest | MultipleChoiceTaskRequest | TextInputTaskRequest,
    Field(discriminator="task_type"),
]


class TeacherTaskOptionResponse(BaseModel):
    id: UUID
    text: str | None
    media_id: UUID | None
    position: int
    is_correct: bool

    @classmethod
    def from_view(cls, option: TaskOptionEditorView) -> "TeacherTaskOptionResponse":
        return cls(
            id=option.id,
            text=option.text,
            media_id=option.media_id,
            position=option.position,
            is_correct=option.is_correct,
        )


class TeacherTaskResponse(BaseModel):
    id: UUID
    lesson_id: UUID
    task_type: TaskType
    position: int
    prompt: str
    prompt_media_id: UUID | None
    explanation: str
    result_media_id: UUID | None
    options: list[TeacherTaskOptionResponse]
    accepted_answers: list[str]

    @classmethod
    def from_view(cls, task: TeacherTaskView) -> "TeacherTaskResponse":
        return cls(
            id=task.id,
            lesson_id=task.lesson_id,
            task_type=task.task_type,
            position=task.position,
            prompt=task.prompt,
            prompt_media_id=task.prompt_media_id,
            explanation=task.explanation,
            result_media_id=task.result_media_id,
            options=[TeacherTaskOptionResponse.from_view(option) for option in task.options],
            accepted_answers=list(task.accepted_answers),
        )


class LearnerTaskOptionResponse(BaseModel):
    id: UUID
    text: str | None
    media_id: UUID | None
    position: int

    @classmethod
    def from_view(cls, option: LearnerTaskOptionView) -> "LearnerTaskOptionResponse":
        return cls(
            id=option.id,
            text=option.text,
            media_id=option.media_id,
            position=option.position,
        )


class LearnerTaskResponse(BaseModel):
    id: UUID
    lesson_id: UUID
    task_type: TaskType
    position: int
    prompt: str
    prompt_media_id: UUID | None
    options: list[LearnerTaskOptionResponse]

    @classmethod
    def from_view(cls, task: LearnerTaskView) -> "LearnerTaskResponse":
        return cls(
            id=task.id,
            lesson_id=task.lesson_id,
            task_type=task.task_type,
            position=task.position,
            prompt=task.prompt,
            prompt_media_id=task.prompt_media_id,
            options=[LearnerTaskOptionResponse.from_view(option) for option in task.options],
        )


class ChoiceAttemptRequest(BaseModel):
    task_type: Literal[TaskType.SINGLE_CHOICE, TaskType.MULTIPLE_CHOICE]
    selected_option_ids: list[UUID]


class TextAttemptRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    task_type: Literal[TaskType.TEXT_INPUT]
    answer_text: str = Field(min_length=1, max_length=10_000)


SubmitAttemptRequest = Annotated[
    ChoiceAttemptRequest | TextAttemptRequest,
    Field(discriminator="task_type"),
]


class AttemptFeedbackResponse(BaseModel):
    attempt_id: UUID
    correct: bool
    explanation: str
    result_media_id: UUID | None
    correct_option_ids: list[UUID]
    first_task_completion: bool
    task_completed: bool
    lesson_completed: bool
    module_completed: bool
    course_completed: bool
    course_progress_percent: int | None

    @classmethod
    def from_view(cls, feedback: AttemptFeedback) -> "AttemptFeedbackResponse":
        return cls(
            attempt_id=feedback.attempt_id,
            correct=feedback.correct,
            explanation=feedback.explanation,
            result_media_id=feedback.result_media_id,
            correct_option_ids=list(feedback.correct_option_ids),
            first_task_completion=feedback.first_task_completion,
            task_completed=feedback.task_completed,
            lesson_completed=feedback.lesson_completed,
            module_completed=feedback.module_completed,
            course_completed=feedback.course_completed,
            course_progress_percent=feedback.course_progress_percent,
        )


@teacher_router.post(
    "/lessons/{lesson_id}/tasks",
    response_model=TeacherTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task in an owned lesson",
    operation_id="createTask",
)
async def create_task(
    lesson_id: UUID,
    payload: CreateTaskRequest,
    teacher: UserView = Depends(require_teacher),
    service: TaskService = Depends(get_task_service),
) -> TeacherTaskResponse:
    data = payload.model_dump()
    data["options"] = [option.model_dump() for option in payload.options]
    task = await service.create_task(author_id=teacher.id, lesson_id=lesson_id, **data)
    return TeacherTaskResponse.from_view(task)


@teacher_router.get(
    "/tasks/{task_id}",
    response_model=TeacherTaskResponse,
    summary="Get an owned task with editor-only correctness data",
    operation_id="getTeacherTask",
)
async def get_teacher_task(
    task_id: UUID,
    teacher: UserView = Depends(require_teacher),
    service: TaskService = Depends(get_task_service),
) -> TeacherTaskResponse:
    return TeacherTaskResponse.from_view(
        await service.teacher_task(author_id=teacher.id, task_id=task_id)
    )


@learning_router.get(
    "/lessons/{lesson_id}/tasks",
    response_model=list[LearnerTaskResponse],
    summary="List learner-safe tasks for a published lesson",
    operation_id="listLearnerLessonTasks",
)
async def list_learner_lesson_tasks(
    lesson_id: UUID,
    _: UserView = Depends(require_authenticated_user),
    service: TaskService = Depends(get_task_service),
) -> list[LearnerTaskResponse]:
    return [
        LearnerTaskResponse.from_view(task)
        for task in await service.learner_tasks(user_id=_.id, lesson_id=lesson_id)
    ]


@learning_router.post(
    "/tasks/{task_id}/attempts",
    response_model=AttemptFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an answer for a published task",
    operation_id="submitTaskAttempt",
)
async def submit_task_attempt(
    task_id: UUID,
    payload: SubmitAttemptRequest = Body(),
    user: UserView = Depends(require_authenticated_user),
    service: TaskService = Depends(get_task_service),
) -> AttemptFeedbackResponse:
    if isinstance(payload, TextAttemptRequest):
        feedback = await service.submit_text_attempt(
            user_id=user.id, task_id=task_id, answer_text=payload.answer_text
        )
    else:
        feedback = await service.submit_choice_attempt(
            user_id=user.id,
            task_id=task_id,
            selected_option_ids=payload.selected_option_ids,
        )
    return AttemptFeedbackResponse.from_view(feedback)
