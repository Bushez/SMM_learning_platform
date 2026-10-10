"""Add teacher-authored feedback to task options.

Revision ID: 7f9c2a0d3b4e
Revises: cf51e8a1d322
Create Date: 2026-10-09
"""

import sqlalchemy as sa
from alembic import op

revision = "7f9c2a0d3b4e"
down_revision = "cf51e8a1d322"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_options", sa.Column("feedback_text", sa.Text(), nullable=True))
    op.add_column("task_options", sa.Column("feedback_media_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_task_options_feedback_media_id_media_assets",
        "task_options",
        "media_assets",
        ["feedback_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_task_options_feedback_media_id_media_assets",
        "task_options",
        type_="foreignkey",
    )
    op.drop_column("task_options", "feedback_media_id")
    op.drop_column("task_options", "feedback_text")
