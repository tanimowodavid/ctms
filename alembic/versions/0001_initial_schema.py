"""Create the initial CTMS schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.create_table(
		"cohort",
		sa.Column("id", sa.String(length=36), nullable=False),
		sa.Column("name", sa.String(length=255), nullable=False),
		sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
		sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
		sa.Column("status", sa.String(length=50), nullable=False),
		sa.Column("embed_token", sa.String(length=255), nullable=False),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("embed_token", name="uq_cohort_embed_token"),
	)
	op.create_table(
		"track",
		sa.Column("id", sa.String(length=36), nullable=False),
		sa.Column("name", sa.String(length=255), nullable=False),
		sa.Column("cohort_id", sa.String(length=36), nullable=False),
		sa.ForeignKeyConstraint(["cohort_id"], ["cohort.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("id", "cohort_id", name="uq_track_id_cohort"),
	)
	op.create_table(
		"application",
		sa.Column("id", sa.String(length=36), nullable=False),
		sa.Column("email", sa.String(length=320), nullable=False),
		sa.Column("full_name", sa.String(length=255), nullable=False),
		sa.Column("status", sa.String(length=20), nullable=False),
		sa.Column("cohort_id", sa.String(length=36), nullable=False),
		sa.Column("track_id", sa.String(length=36), nullable=False),
		sa.Column(
			"created_at",
			sa.DateTime(timezone=True),
			server_default=sa.func.now(),
			nullable=False,
		),
		sa.CheckConstraint(
			"status IN ('PENDING', 'APPROVED', 'REJECTED')",
			name="ck_application_status",
		),
		sa.ForeignKeyConstraint(["cohort_id"], ["cohort.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(
			["track_id", "cohort_id"],
			["track.id", "track.cohort_id"],
			ondelete="RESTRICT",
			name="fk_application_track_cohort",
		),
		sa.PrimaryKeyConstraint("id"),
	)
	op.create_index(
		"uq_application_email_cohort_ci",
		"application",
		[sa.text("lower(trim(email))"), "cohort_id"],
		unique=True,
	)
	op.create_table(
		"profile",
		sa.Column("id", sa.String(length=36), nullable=False),
		sa.Column("email", sa.String(length=320), nullable=False),
		sa.Column("password_hash", sa.String(length=255), nullable=True),
		sa.Column("role", sa.String(length=20), nullable=False),
		sa.Column("status", sa.String(length=20), nullable=False),
		sa.Column("full_name", sa.String(length=255), nullable=False),
		sa.Column("bio", sa.String(), nullable=True),
		sa.Column("tag", sa.String(length=100), nullable=True),
		sa.Column("cohort_id", sa.String(length=36), nullable=True),
		sa.Column("track_id", sa.String(length=36), nullable=True),
		sa.CheckConstraint(
			"role IN ('SUPER_ADMIN', 'ADMIN', 'MENTOR', 'TALENT')",
			name="ck_profile_role",
		),
		sa.CheckConstraint(
			"status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')",
			name="ck_profile_status",
		),
		sa.CheckConstraint(
			"status != 'ACTIVE' OR password_hash IS NOT NULL",
			name="ck_active_profile_password",
		),
		sa.CheckConstraint(
			"role != 'TALENT' OR (cohort_id IS NOT NULL AND track_id IS NOT NULL)",
			name="ck_talent_profile_assignment",
		),
		sa.ForeignKeyConstraint(["cohort_id"], ["cohort.id"], ondelete="RESTRICT"),
		sa.ForeignKeyConstraint(
			["track_id", "cohort_id"],
			["track.id", "track.cohort_id"],
			ondelete="RESTRICT",
			name="fk_profile_track_cohort",
		),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("email", name="uq_profile_email"),
	)
	op.create_table(
		"conversation",
		sa.Column("id", sa.String(length=36), nullable=False),
		sa.Column("conversation_type", sa.String(length=20), nullable=False),
		sa.Column("cohort_id", sa.String(length=36), nullable=True),
		sa.Column("track_id", sa.String(length=36), nullable=True),
		sa.CheckConstraint(
			"(conversation_type = 'GENERAL' AND cohort_id IS NOT NULL AND track_id IS NULL) "
			"OR (conversation_type = 'TRACK' AND track_id IS NOT NULL AND cohort_id IS NULL)",
			name="ck_conversation_target_matches_type",
		),
		sa.ForeignKeyConstraint(["cohort_id"], ["cohort.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["track_id"], ["track.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("cohort_id", name="uq_conversation_cohort"),
		sa.UniqueConstraint("track_id", name="uq_conversation_track"),
	)
	op.create_table(
		"message",
		sa.Column("id", sa.String(length=36), nullable=False),
		sa.Column("conversation_id", sa.String(length=36), nullable=False),
		sa.Column("user_id", sa.String(length=36), nullable=False),
		sa.Column("content", sa.Text(), nullable=False),
		sa.Column(
			"created_at",
			sa.DateTime(timezone=True),
			server_default=sa.func.now(),
			nullable=False,
		),
		sa.ForeignKeyConstraint(["conversation_id"], ["conversation.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["user_id"], ["profile.id"], ondelete="RESTRICT"),
		sa.PrimaryKeyConstraint("id"),
	)


def downgrade() -> None:
	op.drop_table("message")
	op.drop_table("conversation")
	op.drop_table("profile")
	op.drop_index("uq_application_email_cohort_ci", table_name="application")
	op.drop_table("application")
	op.drop_table("track")
	op.drop_table("cohort")
