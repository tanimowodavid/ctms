from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Cohort(Base):
	__tablename__ = "cohort"
	__table_args__ = (UniqueConstraint("embed_token", name="uq_cohort_embed_token"),)

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	status: Mapped[str] = mapped_column(String(50), nullable=False)
	embed_token: Mapped[str] = mapped_column(String(255), nullable=False)

	tracks: Mapped[list["Track"]] = relationship(back_populates="cohort", cascade="all, delete-orphan")
	applications: Mapped[list["Application"]] = relationship(back_populates="cohort", cascade="all, delete-orphan")
	profiles: Mapped[list["Profile"]] = relationship(back_populates="cohort", passive_deletes="all")
	conversation: Mapped["Conversation | None"] = relationship(
		back_populates="cohort", cascade="all, delete-orphan", uselist=False
	)
