from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.sqlalchemy.base import Base


class CourseModel(Base):
    __tablename__ = "courses"
    __table_args__ = (
        Index("ix_courses_author_id", "author_id"),
        Index("ix_courses_status_published_at", "status", "published_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    author_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cover_media_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("media_assets.id", ondelete="RESTRICT")
    )
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False, default="ru")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CourseModuleModel(Base):
    __tablename__ = "course_modules"
    __table_args__ = (
        Index("ix_course_modules_course_position", "course_id", "position", unique=True),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    course_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("courses.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LessonModel(Base):
    __tablename__ = "lessons"
    __table_args__ = (Index("ix_lessons_module_position", "module_id", "position", unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    module_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("course_modules.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskModel(Base):
    __tablename__ = "tasks"
    __table_args__ = (Index("ix_tasks_lesson_position", "lesson_id", "position", unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    lesson_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("lessons.id", ondelete="CASCADE"))
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_media_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("media_assets.id", ondelete="RESTRICT")
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    result_media_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("media_assets.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskOptionModel(Base):
    __tablename__ = "task_options"
    __table_args__ = (Index("ix_task_options_task_position", "task_id", "position", unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"))
    text: Mapped[str | None] = mapped_column(Text)
    media_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("media_assets.id", ondelete="RESTRICT")
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class TaskAcceptedAnswerModel(Base):
    __tablename__ = "task_accepted_answers"
    __table_args__ = (Index("ix_task_accepted_answers_task_id", "task_id"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"))
    normalized_value: Mapped[str] = mapped_column(String(500), nullable=False)


class TaskAttemptModel(Base):
    __tablename__ = "task_attempts"
    __table_args__ = (
        Index("ix_task_attempts_user_task_created_at", "user_id", "task_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    task_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"))
    selected_option_ids: Mapped[list[str] | None] = mapped_column(JSON)
    answer_text: Mapped[str | None] = mapped_column(Text)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CourseEnrollmentModel(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (
        Index("ix_course_enrollments_course_id", "course_id"),
        Index("ix_course_enrollments_user_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    course_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("courses.id", ondelete="RESTRICT"), primary_key=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserTaskProgressModel(Base):
    __tablename__ = "user_task_progress"
    __table_args__ = (Index("ix_user_task_progress_task_id", "task_id"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    task_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tasks.id", ondelete="RESTRICT"), primary_key=True
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
