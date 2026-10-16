from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Application(Base):
	__tablename__ = "application"
	__table_args__ = (
		UniqueConstraint("email", "cohort_id", name="uq_application_email_cohort"),
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
	track_id: Mapped[str] = mapped_column(ForeignKey("track.id", ondelete="RESTRICT"), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

	cohort: Mapped["Cohort"] = relationship(back_populates="applications")
	track: Mapped["Track"] = relationship(back_populates="applications")
