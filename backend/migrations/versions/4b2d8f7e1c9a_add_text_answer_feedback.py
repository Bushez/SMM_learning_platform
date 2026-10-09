"""Add feedback for text-input task answers.

Revision ID: 4b2d8f7e1c9a
Revises: 91d4b7f6e2c8
Create Date: 2026-10-09
"""

from alembic import op
import sqlalchemy as sa


revision = "4b2d8f7e1c9a"
down_revision = "91d4b7f6e2c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("answer_feedback_text", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("answer_feedback_media_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_tasks_answer_feedback_media_id_media_assets", "tasks", "media_assets", ["answer_feedback_media_id"], ["id"], ondelete="RESTRICT")


def downgrade() -> None:
    op.drop_constraint("fk_tasks_answer_feedback_media_id_media_assets", "tasks", type_="foreignkey")
    op.drop_column("tasks", "answer_feedback_media_id")
    op.drop_column("tasks", "answer_feedback_text")
