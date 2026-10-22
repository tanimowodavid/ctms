from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Application, Cohort, Track
from app.schemas.application import PublicApplicationCreate


class CohortEmbedTokenNotFound(Exception):
	pass


class ApplicationIntakeClosed(Exception):
	pass


class ApplicationTrackNotFound(Exception):
	pass


class DuplicateApplication(Exception):
	pass


def get_public_application_options(session: Session, embed_token: str) -> tuple[Cohort, list[Track], bool]:
	cohort = session.scalar(select(Cohort).where(Cohort.embed_token == embed_token))
	if cohort is None:
		raise CohortEmbedTokenNotFound
	tracks = list(session.scalars(select(Track).where(Track.cohort_id == cohort.id).order_by(Track.name, Track.id)))
	accepting = datetime.now(UTC) < cohort.start_date
	return cohort, tracks, accepting


def submit_application(session: Session, embed_token: str, data: PublicApplicationCreate) -> Application:
	cohort = session.scalar(select(Cohort).where(Cohort.embed_token == embed_token))
	if cohort is None:
		raise CohortEmbedTokenNotFound
	if datetime.now(UTC) >= cohort.start_date:
		raise ApplicationIntakeClosed

	track = session.scalar(select(Track).where(Track.id == data.track_id, Track.cohort_id == cohort.id))
	if track is None:
		raise ApplicationTrackNotFound

	duplicate = session.scalar(
		select(Application.id)
		.where(
			Application.cohort_id == cohort.id,
			func.lower(func.trim(Application.email)) == data.email,
		)
		.limit(1)
	)
	if duplicate is not None:
		raise DuplicateApplication

	application = Application(
		full_name=data.full_name,
		email=data.email,
		status="PENDING",
		cohort_id=cohort.id,
		track_id=track.id,
	)
	session.add(application)
	try:
		session.commit()
	except IntegrityError as exc:
		session.rollback()
		constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
		if constraint_name == "uq_application_email_cohort_ci" or "uq_application_email_cohort_ci" in str(exc.orig):
			raise DuplicateApplication from exc
		raise
	session.refresh(application)
	return application
