"""create learning progress tables

Revision ID: ab42c1d0e9f3
Revises: 39b8f3c1d2a4
Create Date: 2026-10-01 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ab42c1d0e9f3"
down_revision: str | None = "39b8f3c1d2a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "course_enrollments",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name=op.f("fk_course_enrollments_course_id_courses"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_course_enrollments_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "course_id", name=op.f("pk_course_enrollments")),
    )
    op.create_index(
        "ix_course_enrollments_course_id", "course_enrollments", ["course_id"], unique=False
    )
    op.create_index(
        "ix_course_enrollments_user_id", "course_enrollments", ["user_id"], unique=False
    )
    op.create_table(
        "user_task_progress",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_user_task_progress_task_id_tasks"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_task_progress_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "task_id", name=op.f("pk_user_task_progress")),
    )
    op.create_index(
        "ix_user_task_progress_task_id", "user_task_progress", ["task_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_user_task_progress_task_id", table_name="user_task_progress")
    op.drop_table("user_task_progress")
    op.drop_index("ix_course_enrollments_user_id", table_name="course_enrollments")
    op.drop_index("ix_course_enrollments_course_id", table_name="course_enrollments")
    op.drop_table("course_enrollments")
