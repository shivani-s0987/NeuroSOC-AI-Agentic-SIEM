"""enterprise authentication sessions and audit

Revision ID: f0c2a4d1b9e7
Revises: efbc1c8b5938
Create Date: 2026-10-31 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f0c2a4d1b9e7"
down_revision: Union[str, None] = "efbc1c8b5938"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_token_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("family_id", sa.String(length=64), nullable=False),
        sa.Column("replaced_by_hash", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("device", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_token_sessions_user_id", "refresh_token_sessions", ["user_id"])
    op.create_index("ix_refresh_token_sessions_token_hash", "refresh_token_sessions", ["token_hash"])
    op.create_index("ix_refresh_token_sessions_family_id", "refresh_token_sessions", ["family_id"])
    op.create_index("ix_refresh_token_sessions_expires_at", "refresh_token_sessions", ["expires_at"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"])
    op.create_index("ix_password_reset_tokens_expires_at", "password_reset_tokens", ["expires_at"])

    op.execute("UPDATE audit_logs SET details = '{}' WHERE details IS NULL")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE audit_logs ALTER COLUMN details TYPE JSON USING to_json(details)")
        op.alter_column("audit_logs", "details", nullable=False)
    else:
        with op.batch_alter_table("audit_logs") as batch:
            batch.alter_column("details", existing_type=sa.Text(), type_=sa.JSON(), nullable=False)
    op.add_column("audit_logs", sa.Column("target_type", sa.String(length=120), nullable=True))
    op.add_column("audit_logs", sa.Column("target_id", sa.String(length=120), nullable=True))
    op.add_column("audit_logs", sa.Column("request_id", sa.String(length=64), nullable=True))
    op.add_column("audit_logs", sa.Column("outcome", sa.String(length=20), nullable=False, server_default="success"))
    with op.batch_alter_table("audit_logs") as batch:
        batch.add_column(sa.Column("actor_user_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_audit_logs_actor_user_id", "users", ["actor_user_id"], ["id"])
        batch.create_index("ix_audit_logs_actor_user_id", ["actor_user_id"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])

    op.execute("UPDATE users SET role = 'ADMIN' WHERE lower(role) IN ('administrator', 'admin')")
    op.execute("UPDATE users SET role = 'SOC_ANALYST' WHERE lower(role) IN ('analyst', 'soc_analyst')")
    op.execute("UPDATE users SET role = 'SECURITY_VIEWER' WHERE role IS NULL OR lower(role) IN ('viewer', 'security_viewer')")


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'Administrator' WHERE role = 'ADMIN'")
    op.execute("UPDATE users SET role = 'Analyst' WHERE role = 'SOC_ANALYST'")
    op.execute("UPDATE users SET role = 'Viewer' WHERE role = 'SECURITY_VIEWER'")
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    with op.batch_alter_table("audit_logs") as batch:
        batch.drop_constraint("fk_audit_logs_actor_user_id", type_="foreignkey")
        batch.drop_column("actor_user_id")
        batch.drop_column("outcome")
        batch.drop_column("request_id")
        batch.drop_column("target_id")
        batch.drop_column("target_type")
        if op.get_bind().dialect.name == "postgresql":
            op.execute("ALTER TABLE audit_logs ALTER COLUMN details TYPE TEXT USING details::text")
        else:
            batch.alter_column("details", existing_type=sa.JSON(), type_=sa.Text(), nullable=True)
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_token_sessions")
