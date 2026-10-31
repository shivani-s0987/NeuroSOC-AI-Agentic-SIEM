"""detection engine foundation

Revision ID: a31c7e8d2f44
Revises: f0c2a4d1b9e7
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a31c7e8d2f44"
down_revision: Union[str, None] = "f0c2a4d1b9e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("rule_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.String(length=120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["rule_id"], ["rules.rule_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_rule_versions_rule_id", "rule_versions", ["rule_id"])
    op.create_index("ix_rule_versions_id", "rule_versions", ["id"])
    op.add_column("rules", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("rules", sa.Column("severity", sa.String(length=50), nullable=True))
    op.add_column("rules", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    with op.batch_alter_table("detections") as batch:
        batch.add_column(sa.Column("fingerprint", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("event_ids", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("first_observed_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("last_observed_at", sa.DateTime(), nullable=True))
        batch.create_index("ix_detections_fingerprint", ["fingerprint"])
        batch.create_unique_constraint("uq_detections_fingerprint", ["fingerprint"])
    op.add_column("alerts", sa.Column("fingerprint", sa.String(length=255), nullable=True))
    op.add_column("alerts", sa.Column("first_observed_at", sa.DateTime(), nullable=True))
    op.add_column("alerts", sa.Column("last_observed_at", sa.DateTime(), nullable=True))
    op.create_index("ix_alerts_fingerprint", "alerts", ["fingerprint"])


def downgrade() -> None:
    op.drop_index("ix_rule_versions_id", table_name="rule_versions")
    op.drop_index("ix_rule_versions_rule_id", table_name="rule_versions")
    op.drop_table("rule_versions")
    op.drop_index("ix_alerts_fingerprint", table_name="alerts")
    op.drop_column("alerts", "last_observed_at")
    op.drop_column("alerts", "first_observed_at")
    op.drop_column("alerts", "fingerprint")
    with op.batch_alter_table("detections") as batch:
        batch.drop_constraint("uq_detections_fingerprint", type_="unique")
        batch.drop_index("ix_detections_fingerprint")
        batch.drop_column("last_observed_at")
        batch.drop_column("first_observed_at")
        batch.drop_column("event_ids")
        batch.drop_column("fingerprint")
    op.drop_column("rules", "version")
    op.drop_column("rules", "severity")
    op.drop_column("rules", "description")
