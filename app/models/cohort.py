from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
	from .application import Application
	from .messaging import Conversation
	from .profile import Profile
	from .track import Track


class Cohort(Base):
	__tablename__ = "cohort"
	__table_args__ = (UniqueConstraint("embed_token", name="uq_cohort_embed_token"),)

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	status: Mapped[str] = mapped_column(String(50), nullable=False)
	embed_token: Mapped[str] = mapped_column(String(255), nullable=False)

	tracks: Mapped[list[Track]] = relationship(back_populates="cohort", cascade="all, delete-orphan")
	applications: Mapped[list[Application]] = relationship(
		back_populates="cohort",
		cascade="all, delete-orphan",
		foreign_keys="Application.cohort_id",
	)
	profiles: Mapped[list[Profile]] = relationship(
		back_populates="cohort",
		passive_deletes="all",
		foreign_keys="Profile.cohort_id",
	)
	conversation: Mapped[Conversation | None] = relationship(
		back_populates="cohort",
		cascade="all, delete-orphan",
		foreign_keys="Conversation.cohort_id",
		uselist=False,
	)
