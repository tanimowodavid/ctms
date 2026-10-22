from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PasswordSetupToken(Base):
	__tablename__ = "password_setup_token"
	__table_args__ = (UniqueConstraint("profile_id", name="uq_password_setup_token_profile"),)

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	profile_id: Mapped[str] = mapped_column(ForeignKey("profile.id", ondelete="CASCADE"), nullable=False)
	token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
	expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EmailOutbox(Base):
	__tablename__ = "email_outbox"
	__table_args__ = (
		CheckConstraint("status IN ('PENDING', 'SENT')", name="ck_email_outbox_status"),
		UniqueConstraint("profile_id", "event_type", name="uq_email_outbox_profile_event"),
		Index("ix_email_outbox_due", "status", "next_attempt_at"),
	)

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	profile_id: Mapped[str] = mapped_column(ForeignKey("profile.id", ondelete="CASCADE"), nullable=False)
	event_type: Mapped[str] = mapped_column(String(50), nullable=False)
	status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", server_default="PENDING")
	attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
	next_attempt_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), server_default=func.now()
	)
	last_error: Mapped[str | None] = mapped_column(Text)
	sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
