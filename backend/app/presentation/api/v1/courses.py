from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.application.auth.dto import UserView
from app.application.courses import CourseService
from app.application.courses.dto import CourseView, LessonView, ModuleView, TeacherCourseOutlineView
from app.domain.courses import CourseStatus
from app.presentation.api.dependencies import (
    get_course_service,
    require_teacher,
)

catalog_router = APIRouter(prefix="/courses", tags=["Courses"])
teacher_router = APIRouter(prefix="/teacher/courses", tags=["Teacher"])


class CourseResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    description: str
    cover_media_id: UUID | None
    category: str
    language_code: str
    status: CourseStatus

    @classmethod
    def from_view(cls, course: CourseView) -> "CourseResponse":
        return cls(
            id=course.id,
            title=course.title,
            slug=course.slug,
            description=course.description,
            cover_media_id=course.cover_media_id,
            category=course.category,
            language_code=course.language_code,
            status=course.status,
        )


class CreateCourseRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=1, max_length=10_000)
    category: str = Field(min_length=2, max_length=80)
    language_code: str = Field(default="ru", min_length=2, max_length=16)


class UpdateCourseRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=2, max_length=160)
    slug: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, min_length=1, max_length=10_000)
    cover_media_id: UUID | None = None
    category: str | None = Field(default=None, min_length=2, max_length=80)
    language_code: str | None = Field(default=None, min_length=2, max_length=16)


class CreateModuleRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=10_000)
    position: int = Field(ge=1)


class UpdateModuleRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=10_000)


class MoveRequest(BaseModel):
    position: int = Field(ge=1)


class ModuleResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    position: int

    @classmethod
    def from_view(cls, module: ModuleView) -> "ModuleResponse":
        return cls(
            id=module.id,
            course_id=module.course_id,
            title=module.title,
            description=module.description,
            position=module.position,
        )


class CreateLessonRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=10_000)
    position: int = Field(ge=1)


class UpdateLessonRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=10_000)


class LessonResponse(BaseModel):
    id: UUID
    module_id: UUID
    title: str
    description: str | None
    position: int

    @classmethod
    def from_view(cls, lesson: LessonView) -> "LessonResponse":
        return cls(
            id=lesson.id,
            module_id=lesson.module_id,
            title=lesson.title,
            description=lesson.description,
            position=lesson.position,
        )


class TeacherCourseOutlineResponse(BaseModel):
    course: CourseResponse
    modules: list[ModuleResponse]
    lessons: list[LessonResponse]

    @classmethod
    def from_view(cls, outline: TeacherCourseOutlineView) -> "TeacherCourseOutlineResponse":
        return cls(
            course=CourseResponse.from_view(outline.course),
            modules=[ModuleResponse.from_view(module) for module in outline.modules],
            lessons=[LessonResponse.from_view(lesson) for lesson in outline.lessons],
        )


@catalog_router.get(
    "",
    response_model=list[CourseResponse],
    summary="List published courses",
    operation_id="listCourses",
)
async def list_courses(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: CourseService = Depends(get_course_service),
) -> list[CourseResponse]:
    return [
        CourseResponse.from_view(course)
        for course in await service.list_catalog(limit=limit, offset=offset)
    ]


@catalog_router.get(
    "/{slug}",
    response_model=CourseResponse,
    summary="Get published course",
    operation_id="getCourseBySlug",
)
async def get_course(
    slug: str, service: CourseService = Depends(get_course_service)
) -> CourseResponse:
    return CourseResponse.from_view(await service.learner_course(slug))


@teacher_router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create course draft",
    operation_id="createCourse",
)
async def create_course(
    payload: CreateCourseRequest,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    return CourseResponse.from_view(
        await service.create_course(author_id=teacher.id, **payload.model_dump())
    )


@teacher_router.get(
    "",
    response_model=list[CourseResponse],
    summary="List own courses",
    operation_id="listTeacherCourses",
)
async def list_teacher_courses(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> list[CourseResponse]:
    courses = await service.list_teacher_courses(author_id=teacher.id, limit=limit, offset=offset)
    return [CourseResponse.from_view(course) for course in courses]


@teacher_router.patch(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Update own course",
    operation_id="updateCourse",
)
async def update_course(
    course_id: UUID,
    payload: UpdateCourseRequest,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    return CourseResponse.from_view(
        await service.update_course(
            author_id=teacher.id,
            course_id=course_id,
            **payload.model_dump(exclude_none=True),
        )
    )


@teacher_router.get(
    "/{course_id}/outline",
    response_model=TeacherCourseOutlineResponse,
    summary="Get own course outline for the builder",
    operation_id="getTeacherCourseOutline",
)
async def get_teacher_course_outline(
    course_id: UUID,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> TeacherCourseOutlineResponse:
    return TeacherCourseOutlineResponse.from_view(
        await service.teacher_outline(author_id=teacher.id, course_id=course_id)
    )


@teacher_router.post(
    "/{course_id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add module to own course",
    operation_id="createCourseModule",
)
async def create_module(
    course_id: UUID,
    payload: CreateModuleRequest,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> ModuleResponse:
    return ModuleResponse.from_view(
        await service.add_module(author_id=teacher.id, course_id=course_id, **payload.model_dump())
    )


@teacher_router.patch(
    "/modules/{module_id}",
    response_model=ModuleResponse,
    summary="Update own module",
    operation_id="updateCourseModule",
)
async def update_module(
    module_id: UUID,
    payload: UpdateModuleRequest,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> ModuleResponse:
    return ModuleResponse.from_view(
        await service.update_module(
            author_id=teacher.id, module_id=module_id, **payload.model_dump()
        )
    )


@teacher_router.delete(
    "/modules/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete own empty-progress module",
    operation_id="deleteCourseModule",
)
async def delete_module(
    module_id: UUID,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> None:
    await service.delete_module(author_id=teacher.id, module_id=module_id)


@teacher_router.post(
    "/modules/{module_id}/move",
    response_model=ModuleResponse,
    summary="Move own module",
    operation_id="moveCourseModule",
)
async def move_module(
    module_id: UUID,
    payload: MoveRequest,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> ModuleResponse:
    return ModuleResponse.from_view(
        await service.move_module(
            author_id=teacher.id, module_id=module_id, position=payload.position
        )
    )


@teacher_router.post(
    "/modules/{module_id}/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add lesson to own course module",
    operation_id="createLesson",
)
async def create_lesson(
    module_id: UUID,
    payload: CreateLessonRequest,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> LessonResponse:
    return LessonResponse.from_view(
        await service.add_lesson(author_id=teacher.id, module_id=module_id, **payload.model_dump())
    )


@teacher_router.patch(
    "/lessons/{lesson_id}",
    response_model=LessonResponse,
    summary="Update own lesson",
    operation_id="updateCourseLesson",
)
async def update_lesson(
    lesson_id: UUID,
    payload: UpdateLessonRequest,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> LessonResponse:
    return LessonResponse.from_view(
        await service.update_lesson(
            author_id=teacher.id, lesson_id=lesson_id, **payload.model_dump()
        )
    )


@teacher_router.delete(
    "/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete own empty-progress lesson",
    operation_id="deleteCourseLesson",
)
async def delete_lesson(
    lesson_id: UUID,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> None:
    await service.delete_lesson(author_id=teacher.id, lesson_id=lesson_id)


@teacher_router.post(
    "/lessons/{lesson_id}/move",
    response_model=LessonResponse,
    summary="Move own lesson",
    operation_id="moveCourseLesson",
)
async def move_lesson(
    lesson_id: UUID,
    payload: MoveRequest,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> LessonResponse:
    return LessonResponse.from_view(
        await service.move_lesson(
            author_id=teacher.id, lesson_id=lesson_id, position=payload.position
        )
    )


@teacher_router.post(
    "/{course_id}/publish",
    response_model=CourseResponse,
    summary="Publish own course",
    operation_id="publishCourse",
)
async def publish_course(
    course_id: UUID,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    return CourseResponse.from_view(
        await service.publish(author_id=teacher.id, course_id=course_id)
    )


@teacher_router.post(
    "/{course_id}/archive",
    response_model=CourseResponse,
    summary="Archive own course without deleting learner progress",
    operation_id="archiveCourse",
)
async def archive_course(
    course_id: UUID,
    teacher: UserView = Depends(require_teacher),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    return CourseResponse.from_view(
        await service.archive(author_id=teacher.id, course_id=course_id)
    )
