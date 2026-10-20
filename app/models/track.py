from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
	from .application import Application
	from .cohort import Cohort
	from .messaging import Conversation
	from .profile import Profile


class Track(Base):
	__tablename__ = "track"
	__table_args__ = (
		UniqueConstraint("id", "cohort_id", name="uq_track_id_cohort"),
	)

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	cohort_id: Mapped[str] = mapped_column(ForeignKey("cohort.id", ondelete="CASCADE"), nullable=False)

	cohort: Mapped[Cohort] = relationship(back_populates="tracks", foreign_keys=[cohort_id])
	applications: Mapped[list[Application]] = relationship(
		back_populates="track",
		foreign_keys="Application.track_id",
	)
	profiles: Mapped[list[Profile]] = relationship(
		back_populates="track",
		passive_deletes="all",
		foreign_keys="Profile.track_id",
	)
	conversation: Mapped[Conversation | None] = relationship(
		back_populates="track",
		cascade="all, delete-orphan",
		foreign_keys="Conversation.track_id",
		uselist=False,
	)
