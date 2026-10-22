"""Add durable staff onboarding tokens and email outbox.

Revision ID: 0002_staff_onboarding
Revises: 0001_initial
Create Date: 2026-10-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_staff_onboarding"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.create_index("uq_profile_email_normalized", "profile", [sa.text("lower(trim(email))")], unique=True)
	op.create_table(
		"password_setup_token",
		sa.Column("id", sa.String(length=36), nullable=False),
		sa.Column("profile_id", sa.String(length=36), nullable=False),
		sa.Column("token_hash", sa.String(length=64), nullable=False),
		sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
		sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.ForeignKeyConstraint(["profile_id"], ["profile.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("profile_id", name="uq_password_setup_token_profile"),
		sa.UniqueConstraint("token_hash"),
	)
	op.create_table(
		"email_outbox",
		sa.Column("id", sa.String(length=36), nullable=False),
		sa.Column("profile_id", sa.String(length=36), nullable=False),
		sa.Column("event_type", sa.String(length=50), nullable=False),
		sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
		sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
		sa.Column("next_attempt_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.Column("last_error", sa.Text(), nullable=True),
		sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.CheckConstraint("status IN ('PENDING', 'SENT')", name="ck_email_outbox_status"),
		sa.ForeignKeyConstraint(["profile_id"], ["profile.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("profile_id", "event_type", name="uq_email_outbox_profile_event"),
	)
	op.create_index("ix_email_outbox_due", "email_outbox", ["status", "next_attempt_at"])


def downgrade() -> None:
	op.drop_index("ix_email_outbox_due", table_name="email_outbox")
	op.drop_table("email_outbox")
	op.drop_table("password_setup_token")
	op.drop_index("uq_profile_email_normalized", table_name="profile")
