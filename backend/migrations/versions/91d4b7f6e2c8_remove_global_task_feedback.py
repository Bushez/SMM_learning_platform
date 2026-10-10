"""Remove deprecated global task feedback.

Revision ID: 91d4b7f6e2c8
Revises: 7f9c2a0d3b4e
Create Date: 2026-10-09
"""

import sqlalchemy as sa
from alembic import op

revision = "91d4b7f6e2c8"
down_revision = "7f9c2a0d3b4e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("fk_tasks_result_media_id_media_assets", "tasks", type_="foreignkey")
    op.drop_column("tasks", "result_media_id")
    op.drop_column("tasks", "explanation")


def downgrade() -> None:
    op.add_column("tasks", sa.Column("explanation", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("result_media_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_result_media_id_media_assets",
        "tasks",
        "media_assets",
        ["result_media_id"],
        ["id"],
        ondelete="RESTRICT",
    )
