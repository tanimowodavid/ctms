from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Application, Cohort, EmailOutbox, Profile, Track
from app.schemas.application import PublicApplicationCreate


class CohortEmbedTokenNotFound(Exception):
	pass


class ApplicationIntakeClosed(Exception):
	pass


class ApplicationTrackNotFound(Exception):
	pass


class DuplicateApplication(Exception):
	pass


class ApplicationNotFound(Exception):
	pass


class ApplicationAlreadyProcessed(Exception):
	pass


class ApplicationProfileConflict(Exception):
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


def list_applications(
	session: Session, *, cohort_id: str | None = None, status: str | None = None
) -> list[Application]:
	query = select(Application).order_by(Application.created_at.desc(), Application.id)
	if cohort_id is not None:
		query = query.where(Application.cohort_id == cohort_id)
	if status is not None:
		query = query.where(Application.status == status)
	return list(session.scalars(query))


def get_application(session: Session, application_id: str) -> Application:
	application = session.get(Application, application_id)
	if application is None:
		raise ApplicationNotFound
	return application


def approve_application(session: Session, application_id: str) -> tuple[Application, Profile]:
	application = session.scalar(select(Application).where(Application.id == application_id).with_for_update())
	if application is None:
		raise ApplicationNotFound
	if application.status != "PENDING":
		raise ApplicationAlreadyProcessed

	profile_exists = session.scalar(
		select(Profile.id)
		.where(func.lower(func.trim(Profile.email)) == application.email)
		.limit(1)
	)
	if profile_exists is not None:
		raise ApplicationProfileConflict

	profile = Profile(
		email=application.email.strip().lower(),
		full_name=application.full_name,
		role="TALENT",
		status="INACTIVE",
		tag="TALENT",
		cohort_id=application.cohort_id,
		track_id=application.track_id,
	)
	session.add(profile)
	try:
		session.flush()
		application.status = "APPROVED"
		session.add(EmailOutbox(profile_id=profile.id, event_type="TALENT_PASSWORD_SETUP"))
		session.commit()
	except IntegrityError as exc:
		session.rollback()
		if "uq_profile_email_normalized" in str(exc.orig) or "uq_profile_email" in str(exc.orig):
			raise ApplicationProfileConflict from exc
		raise
	session.refresh(application)
	session.refresh(profile)
	return application, profile


def reject_application(session: Session, application_id: str) -> Application:
	application = session.scalar(select(Application).where(Application.id == application_id).with_for_update())
	if application is None:
		raise ApplicationNotFound
	if application.status != "PENDING":
		raise ApplicationAlreadyProcessed
	application.status = "REJECTED"
	session.commit()
	session.refresh(application)
	return application
