"""create media assets

Revision ID: 8e79bff1e71f
Revises: 2c58a20b5495
Create Date: 2026-10-01 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8e79bff1e71f"
down_revision: str | None = "2c58a20b5495"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("object_key", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_media_assets_owner_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media_assets")),
        sa.UniqueConstraint("object_key", name=op.f("uq_media_assets_object_key")),
    )
    op.create_index(
        "ix_media_assets_owner_id_created_at",
        "media_assets",
        ["owner_id", "created_at"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_courses_cover_media_id_media_assets"),
        "courses",
        "media_assets",
        ["cover_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        op.f("fk_tasks_prompt_media_id_media_assets"),
        "tasks",
        "media_assets",
        ["prompt_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        op.f("fk_tasks_result_media_id_media_assets"),
        "tasks",
        "media_assets",
        ["result_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        op.f("fk_task_options_media_id_media_assets"),
        "task_options",
        "media_assets",
        ["media_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_task_options_media_id_media_assets"), "task_options", type_="foreignkey"
    )
    op.drop_constraint(op.f("fk_tasks_result_media_id_media_assets"), "tasks", type_="foreignkey")
    op.drop_constraint(op.f("fk_tasks_prompt_media_id_media_assets"), "tasks", type_="foreignkey")
    op.drop_constraint(
        op.f("fk_courses_cover_media_id_media_assets"), "courses", type_="foreignkey"
    )
    op.drop_index("ix_media_assets_owner_id_created_at", table_name="media_assets")
    op.drop_table("media_assets")
