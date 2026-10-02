import re
from uuid import UUID

from app.application.common.errors import AuthorizationError, NotFoundError, ValidationError
from app.application.media.ports import MediaRepository
from app.domain.courses import CourseStatus

from .dto import CourseView, LessonView, ModuleView, TeacherCourseOutlineView
from .ports import CourseRepository, CourseTransaction


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "course"


class CourseService:
    def __init__(
        self,
        *,
        courses: CourseRepository,
        media: MediaRepository,
        transaction: CourseTransaction,
    ) -> None:
        self._courses = courses
        self._media = media
        self._transaction = transaction

    async def create_course(
        self,
        *,
        author_id: UUID,
        title: str,
        slug: str,
        description: str,
        category: str,
        language_code: str,
    ) -> CourseView:
        course = await self._courses.create_course(
            author_id=author_id,
            title=title.strip(),
            slug=slugify(slug),
            description=description.strip(),
            category=category.strip(),
            language_code=language_code,
        )
        await self._transaction.commit()
        return course

    async def list_catalog(self, *, limit: int, offset: int) -> list[CourseView]:
        return await self._courses.list_published(limit=limit, offset=offset)

    async def learner_course(self, slug: str) -> CourseView:
        course = await self._courses.get_by_slug(slug)
        if course is None or course.status != CourseStatus.PUBLISHED:
            raise NotFoundError("Published course not found")
        return course

    async def list_teacher_courses(
        self, *, author_id: UUID, limit: int, offset: int
    ) -> list[CourseView]:
        return await self._courses.list_by_author(author_id=author_id, limit=limit, offset=offset)

    async def teacher_course(self, *, author_id: UUID, course_id: UUID) -> CourseView:
        course = await self._courses.get_course(course_id)
        if course is None:
            raise NotFoundError("Course not found")
        if course.author_id != author_id:
            raise AuthorizationError("You do not own this course")
        return course

    async def teacher_outline(
        self, *, author_id: UUID, course_id: UUID
    ) -> TeacherCourseOutlineView:
        course = await self.teacher_course(author_id=author_id, course_id=course_id)
        modules = await self._courses.list_modules(course_id)
        lessons = await self._courses.list_lessons(course_id)
        return TeacherCourseOutlineView(
            course=course,
            modules=tuple(modules),
            lessons=tuple(lessons),
        )

    async def update_course(
        self, *, author_id: UUID, course_id: UUID, **changes: object
    ) -> CourseView:
        await self.teacher_course(author_id=author_id, course_id=course_id)
        if "slug" in changes:
            changes["slug"] = slugify(str(changes["slug"]))
        if "cover_media_id" in changes and changes["cover_media_id"] is not None:
            is_owner = await self._media.is_owned_by(
                media_id=UUID(str(changes["cover_media_id"])), owner_id=author_id
            )
            if not is_owner:
                raise ValidationError("Course cover must be an image uploaded by this teacher")
        course = await self._courses.update_course(course_id, **changes)
        await self._transaction.commit()
        return course

    async def add_module(
        self,
        *,
        author_id: UUID,
        course_id: UUID,
        title: str,
        description: str | None,
        position: int,
    ) -> ModuleView:
        await self.teacher_course(author_id=author_id, course_id=course_id)
        module = await self._courses.add_module(
            course_id=course_id, title=title.strip(), description=description, position=position
        )
        await self._transaction.commit()
        return module

    async def add_lesson(
        self,
        *,
        author_id: UUID,
        module_id: UUID,
        title: str,
        description: str | None,
        position: int,
    ) -> LessonView:
        module = await self._courses.get_module(module_id)
        if module is None:
            raise NotFoundError("Module not found")
        await self.teacher_course(author_id=author_id, course_id=module.course_id)
        lesson = await self._courses.add_lesson(
            module_id=module_id,
            title=title.strip(),
            description=description.strip() if description else None,
            position=position,
        )
        await self._transaction.commit()
        return lesson

    async def publish(self, *, author_id: UUID, course_id: UUID) -> CourseView:
        await self.teacher_course(author_id=author_id, course_id=course_id)
        issues = await self._courses.publish_issues(course_id)
        if issues:
            from app.application.common.errors import ConflictError

            raise ConflictError("Course cannot be published: " + "; ".join(issues))
        course = await self._courses.update_course(
            course_id, status=CourseStatus.PUBLISHED.value, published=True
        )
        await self._transaction.commit()
        return course
