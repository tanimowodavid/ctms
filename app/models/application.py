from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
	from .cohort import Cohort
	from .track import Track


class Application(Base):
	__tablename__ = "application"
	__table_args__ = (
		ForeignKeyConstraint(
			["track_id", "cohort_id"],
			["track.id", "track.cohort_id"],
			ondelete="RESTRICT",
			name="fk_application_track_cohort",
		),
		CheckConstraint(
			"status IN ('PENDING', 'APPROVED', 'REJECTED')",
			name="ck_application_status",
		),
	)

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	email: Mapped[str] = mapped_column(String(320), nullable=False)
	full_name: Mapped[str] = mapped_column(String(255), nullable=False)
	status: Mapped[str] = mapped_column(String(20), nullable=False)
	cohort_id: Mapped[str] = mapped_column(ForeignKey("cohort.id", ondelete="CASCADE"), nullable=False)
	track_id: Mapped[str] = mapped_column(String(36), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

	cohort: Mapped[Cohort] = relationship(back_populates="applications", foreign_keys=[cohort_id])
	track: Mapped[Track] = relationship(back_populates="applications", foreign_keys=[track_id])


Index(
	"uq_application_email_cohort_ci",
	func.lower(func.trim(Application.email)),
	Application.cohort_id,
	unique=True,
)
