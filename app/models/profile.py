from uuid import uuid4

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Profile(Base):
	__tablename__ = "profile"
	__table_args__ = (
		UniqueConstraint("email", name="uq_profile_email"),
		CheckConstraint(
			"role IN ('SUPER_ADMIN', 'ADMIN', 'MENTOR', 'TALENT')",
			name="ck_profile_role",
		),
		CheckConstraint(
			"status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')",
			name="ck_profile_status",
		),
		CheckConstraint(
			"status != 'ACTIVE' OR password_hash IS NOT NULL",
			name="ck_active_profile_password",
		),
		CheckConstraint(
			"role != 'TALENT' OR (cohort_id IS NOT NULL AND track_id IS NOT NULL)",
			name="ck_talent_profile_assignment",
		),
	)

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	email: Mapped[str] = mapped_column(String(320), nullable=False)
	password_hash: Mapped[str | None] = mapped_column(String(255))
	role: Mapped[str] = mapped_column(String(20), nullable=False)
	status: Mapped[str] = mapped_column(String(20), nullable=False)
	full_name: Mapped[str] = mapped_column(String(255), nullable=False)
	bio: Mapped[str | None] = mapped_column(String)
	tag: Mapped[str | None] = mapped_column(String(100))
	cohort_id: Mapped[str | None] = mapped_column(ForeignKey("cohort.id", ondelete="RESTRICT"))
	track_id: Mapped[str | None] = mapped_column(ForeignKey("track.id", ondelete="RESTRICT"))

	cohort: Mapped["Cohort | None"] = relationship(back_populates="profiles")
	track: Mapped["Track | None"] = relationship(back_populates="profiles")
	messages: Mapped[list["Message"]] = relationship(back_populates="user", passive_deletes="all")
