from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Application, Cohort, Profile, Track


def create_cohort(session: Session, name: str) -> Cohort:
	now = datetime.now(UTC)
	cohort = Cohort(
		name=name,
		start_date=now,
		end_date=now + timedelta(days=90),
		status="ACTIVE",
		embed_token=f"widget-{name}",
	)
	session.add(cohort)
	session.flush()
	return cohort


def create_track(session: Session, cohort: Cohort, name: str) -> Track:
	track = Track(name=name, cohort_id=cohort.id)
	session.add(track)
	session.flush()
	return track


def make_application(cohort: Cohort, track: Track, email: str) -> Application:
	return Application(
		email=email,
		full_name="Test Applicant",
		status="PENDING",
		cohort_id=cohort.id,
		track_id=track.id,
	)


def test_application_email_is_unique_ignoring_case_and_outer_spaces(db_session: Session) -> None:
	cohort = create_cohort(db_session, "cohort-one")
	track = create_track(db_session, cohort, "backend")
	db_session.add(make_application(cohort, track, " Person@Example.com "))
	db_session.commit()

	db_session.add(make_application(cohort, track, "person@example.com"))
	with pytest.raises(IntegrityError):
		db_session.commit()


def test_same_application_email_is_allowed_in_a_different_cohort(db_session: Session) -> None:
	first_cohort = create_cohort(db_session, "cohort-one")
	first_track = create_track(db_session, first_cohort, "backend")
	second_cohort = create_cohort(db_session, "cohort-two")
	second_track = create_track(db_session, second_cohort, "backend")
	db_session.add_all(
		[
			make_application(first_cohort, first_track, "person@example.com"),
			make_application(second_cohort, second_track, "PERSON@example.com"),
		]
	)

	db_session.commit()


def test_application_track_must_belong_to_its_cohort(db_session: Session) -> None:
	first_cohort = create_cohort(db_session, "cohort-one")
	second_cohort = create_cohort(db_session, "cohort-two")
	other_cohort_track = create_track(db_session, second_cohort, "backend")
	db_session.add(make_application(first_cohort, other_cohort_track, "person@example.com"))

	with pytest.raises(IntegrityError):
		db_session.commit()


def test_talent_profile_track_must_belong_to_its_cohort(db_session: Session) -> None:
	first_cohort = create_cohort(db_session, "cohort-one")
	second_cohort = create_cohort(db_session, "cohort-two")
	other_cohort_track = create_track(db_session, second_cohort, "backend")
	profile = Profile(
		email="talent@example.com",
		role="TALENT",
		status="INACTIVE",
		full_name="Test Talent",
		cohort_id=first_cohort.id,
		track_id=other_cohort_track.id,
	)
	db_session.add(profile)

	with pytest.raises(IntegrityError):
		db_session.commit()
