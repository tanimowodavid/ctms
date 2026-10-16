from uuid import uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Track(Base):
	__tablename__ = "track"

	id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	cohort_id: Mapped[str] = mapped_column(ForeignKey("cohort.id", ondelete="CASCADE"), nullable=False)

	cohort: Mapped["Cohort"] = relationship(back_populates="tracks")
	applications: Mapped[list["Application"]] = relationship(back_populates="track")
	profiles: Mapped[list["Profile"]] = relationship(back_populates="track", passive_deletes="all")
	conversation: Mapped["Conversation | None"] = relationship(
		back_populates="track", cascade="all, delete-orphan", uselist=False
	)
