"""Add realtime processing state and notifications.

Revision ID: b7c2e1d6f901
Revises: 4e1a7c2d9f60
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7c2e1d6f901"
down_revision: Union[str, None] = "4e1a7c2d9f60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for name, type_, default in (
        ("external_id", sa.String(length=255), None),
        ("idempotency_key", sa.String(length=255), None),
        ("ingestion_status", sa.String(length=50), "accepted"),
        ("processing_status", sa.String(length=50), "pending"),
        ("last_processing_error", sa.Text(), None),
    ):
        op.add_column("events", sa.Column(name, type_, nullable=False if default else True, server_default=default))
    op.add_column("events", sa.Column("processed_at", sa.DateTime(), nullable=True))
    op.add_column("events", sa.Column("processing_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_events_external_id", "events", ["external_id"], unique=True)
    op.create_index("ix_events_idempotency_key", "events", ["idempotency_key"], unique=True)

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("claimed_by", sa.String(length=255), nullable=True),
        sa.Column("terminal_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_processing_jobs_event_id", "processing_jobs", ["event_id"], unique=True)
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])
    op.create_index("ix_processing_jobs_next_attempt_at", "processing_jobs", ["next_attempt_at"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("notification_id", sa.String(length=255), nullable=False, unique=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
    )
    op.create_index("ix_notifications_notification_id", "notifications", ["notification_id"], unique=True)
    op.create_index("ix_notifications_event_type", "notifications", ["event_type"])
    op.create_index("ix_notifications_timestamp", "notifications", ["timestamp"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("processing_jobs")
    for name in ("external_id", "idempotency_key", "ingestion_status", "processing_status", "processed_at",
                 "processing_attempts", "last_processing_error"):
        op.drop_column("events", name)
