"""Add threat intelligence indicators and event matches.

Revision ID: c6d8a2f4e103
Revises: b7c2e1d6f901
"""
from alembic import op
import sqlalchemy as sa


revision = "c6d8a2f4e103"
down_revision = "b7c2e1d6f901"


def upgrade() -> None:
    columns = [
        sa.Column("normalized_value", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(120), nullable=False, server_default="manual"),
        sa.Column("original_value", sa.String(255), nullable=True),
        sa.Column("first_seen", sa.DateTime(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("valid_from", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("active", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("external_reference", sa.String(500), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    ]
    for column in columns:
        op.add_column("threat_intel", column)
    op.execute("UPDATE threat_intel SET normalized_value = lower(indicator), original_value = indicator WHERE normalized_value IS NULL")
    op.create_index("ix_threat_intel_normalized_value", "threat_intel", ["normalized_value"], unique=True)

    for column in (
        sa.Column("platforms", sa.JSON(), nullable=True),
        sa.Column("data_sources", sa.JSON(), nullable=True),
        sa.Column("detection", sa.Text(), nullable=True),
        sa.Column("tactics", sa.JSON(), nullable=True),
        sa.Column("parent_technique_id", sa.String(80), nullable=True),
        sa.Column("external_url", sa.String(500), nullable=True),
        sa.Column("revoked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deprecated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stix_id", sa.String(255), nullable=True),
    ):
        op.add_column("mitre_techniques", column)
    op.create_index("ix_mitre_techniques_parent_technique_id", "mitre_techniques", ["parent_technique_id"])

    op.create_table(
        "ioc_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("indicator_id", sa.Integer(), sa.ForeignKey("threat_intel.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("match_type", sa.String(80), nullable=False),
        sa.Column("matched_field", sa.String(120), nullable=False),
        sa.Column("matched_value", sa.String(255), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(80), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.Column("matched_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("event_id", "indicator_id", "matched_field", name="uq_ioc_event_match"),
    )
    op.create_index("ix_ioc_matches_event_id", "ioc_matches", ["event_id"])
    op.create_index("ix_ioc_matches_indicator_id", "ioc_matches", ["indicator_id"])
    op.create_index("ix_ioc_matches_alert_id", "ioc_matches", ["alert_id"])


def downgrade() -> None:
    op.drop_table("ioc_matches")
    op.drop_index("ix_mitre_techniques_parent_technique_id", table_name="mitre_techniques")
