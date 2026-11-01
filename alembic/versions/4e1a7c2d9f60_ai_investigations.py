"""add AI investigations

Revision ID: 4e1a7c2d9f60
Revises: a31c7e8d2f44
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4e1a7c2d9f60"
down_revision: Union[str, None] = "a31c7e8d2f44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("initiated_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_category", sa.String(length=80), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("rerun_of", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rerun_of"], ["investigations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigations_id", "investigations", ["id"])
    op.create_index("ix_investigations_alert_id", "investigations", ["alert_id"])
    op.create_index("ix_investigations_case_id", "investigations", ["case_id"])
    op.create_index("ix_investigations_initiated_by", "investigations", ["initiated_by"])
    op.create_index("ix_investigations_status", "investigations", ["status"])
    op.create_table(
        "investigation_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("evidence_references", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("investigation_id", name="uq_investigation_result"),
    )
    op.create_index("ix_investigation_results_id", "investigation_results", ["id"])
    op.create_index("ix_investigation_results_investigation_id", "investigation_results", ["investigation_id"])
    op.create_table(
        "investigation_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigation_feedback_id", "investigation_feedback", ["id"])
    op.create_index("ix_investigation_feedback_investigation_id", "investigation_feedback", ["investigation_id"])
    op.create_index("ix_investigation_feedback_user_id", "investigation_feedback", ["user_id"])


def downgrade() -> None:
    op.drop_table("investigation_feedback")
    op.drop_table("investigation_results")
    op.drop_table("investigations")
