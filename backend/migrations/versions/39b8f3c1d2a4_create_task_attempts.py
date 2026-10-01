"""create task attempts

Revision ID: 39b8f3c1d2a4
Revises: 8e79bff1e71f
Create Date: 2026-10-01 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "39b8f3c1d2a4"
down_revision: str | None = "8e79bff1e71f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "task_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("selected_option_ids", sa.JSON(), nullable=True),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_task_attempts_task_id_tasks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_task_attempts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_attempts")),
    )
    op.create_index(
        "ix_task_attempts_user_task_created_at",
        "task_attempts",
        ["user_id", "task_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_task_attempts_user_task_created_at", table_name="task_attempts")
    op.drop_table("task_attempts")
