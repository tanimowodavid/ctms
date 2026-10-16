from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Conversation(Base):
	__tablename__ = "conversation"
	__table_args__ = (
		UniqueConstraint("cohort_id", name="uq_conversation_cohort"),
		UniqueConstraint("track_id", name="uq_conversation_track"),
		CheckConstraint(
			"(conversation_type = 'GENERAL' AND cohort_id IS NOT NULL AND track_id IS NULL) "
			"OR (conversation_type = 'TRACK' AND track_id IS NOT NULL AND cohort_id IS NULL)",
			name="ck_conversation_target_matches_type",
		),
	)

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	conversation_type: Mapped[str] = mapped_column(String(20), nullable=False)
	cohort_id: Mapped[str | None] = mapped_column(ForeignKey("cohort.id", ondelete="CASCADE"))
	track_id: Mapped[str | None] = mapped_column(ForeignKey("track.id", ondelete="CASCADE"))

	cohort: Mapped["Cohort | None"] = relationship(back_populates="conversation")
	track: Mapped["Track | None"] = relationship(back_populates="conversation")
	messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
	__tablename__ = "message"

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	conversation_id: Mapped[str] = mapped_column(ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False)
	user_id: Mapped[str] = mapped_column(ForeignKey("profile.id", ondelete="RESTRICT"), nullable=False)
	content: Mapped[str] = mapped_column(Text, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

	conversation: Mapped["Conversation"] = relationship(back_populates="messages")
	user: Mapped["Profile"] = relationship(back_populates="messages")
