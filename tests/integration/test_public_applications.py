from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import Settings
from app.main import app, create_app
from app.models import Application, Cohort, Track


def add_cohort(session: Session, *, token: str, starts_in: timedelta) -> tuple[Cohort, Track, Track]:
	start = datetime.now(UTC) + starts_in
	cohort = Cohort(
		name="Public Applications",
		start_date=start,
		end_date=start + timedelta(days=60),
		status="ACTIVE",
		embed_token=token,
	)
	cohort.tracks = [Track(name="Backend"), Track(name="Frontend")]
	session.add(cohort)
	session.commit()
	return cohort, cohort.tracks[0], cohort.tracks[1]


def client_for(session: Session) -> TestClient:
	def override_db():
		yield session

	app.dependency_overrides[get_db] = override_db
	return TestClient(app)


def test_public_application_options_submission_normalization_and_rejections(db_session: Session) -> None:
	cohort, backend, frontend = add_cohort(db_session, token="public-widget-token", starts_in=timedelta(days=2))
	closed_cohort, closed_track, _ = add_cohort(
		db_session, token="closed-widget-token", starts_in=timedelta(seconds=-1)
	)
	client = client_for(db_session)
	try:
		options = client.get(f"/api/v1/cohorts/{cohort.embed_token}/application-tracks")
		assert options.status_code == 200
		assert options.json()["cohortName"] == cohort.name
		assert options.json()["acceptingApplications"] is True
		assert {track["id"] for track in options.json()["tracks"]} == {backend.id, frontend.id}
		assert client.get("/api/v1/cohorts/unknown-token/application-tracks").status_code == 404

		payload = {"fullName": "  Jane Doe  ", "email": " Jane.Doe@Example.COM ", "trackId": backend.id}
		submitted = client.post(f"/api/v1/cohorts/{cohort.embed_token}/apply", json=payload)
		assert submitted.status_code == 201, submitted.text
		assert submitted.json()["status"] == "PENDING"
		assert submitted.json()["message"] == "Application submitted successfully"
		application = db_session.get(Application, submitted.json()["applicationId"])
		assert application.full_name == "Jane Doe"
		assert application.email == "jane.doe@example.com"

		duplicate = client.post(
			f"/api/v1/cohorts/{cohort.embed_token}/apply",
			json={"fullName": "Jane Again", "email": "jane.doe@example.com", "trackId": frontend.id},
		)
		assert duplicate.status_code == 409

		wrong_track = client.post(
			f"/api/v1/cohorts/{cohort.embed_token}/apply",
			json={"fullName": "Other Applicant", "email": "other@example.com", "trackId": closed_track.id},
		)
		assert wrong_track.status_code == 400

		invalid_email = client.post(
			f"/api/v1/cohorts/{cohort.embed_token}/apply",
			json={"fullName": "Invalid Email", "email": "not-an-email", "trackId": backend.id},
		)
		assert invalid_email.status_code == 400

		closed = client.post(
			f"/api/v1/cohorts/{closed_cohort.embed_token}/apply",
			json={"fullName": "Late Applicant", "email": "late@example.com", "trackId": closed_track.id},
		)
		assert closed.status_code == 409
		assert db_session.scalar(select(func.count(Application.id))) == 1
	finally:
		app.dependency_overrides.clear()


def test_concurrent_duplicate_insert_is_returned_as_conflict(db_session: Session, monkeypatch) -> None:
	cohort, backend, _ = add_cohort(db_session, token="concurrent-widget-token", starts_in=timedelta(days=2))
	client = client_for(db_session)
	original_commit = db_session.commit

	def commit_after_competing_insert() -> None:
		with Session(db_session.bind) as competing_session:
			competing_session.add(
				Application(
					full_name="First Request",
					email="same@example.com",
					status="PENDING",
					cohort_id=cohort.id,
					track_id=backend.id,
				)
			)
			competing_session.commit()
		original_commit()

	monkeypatch.setattr(db_session, "commit", commit_after_competing_insert)
	try:
		response = client.post(
			f"/api/v1/cohorts/{cohort.embed_token}/apply",
			json={"fullName": "Second Request", "email": "same@example.com", "trackId": backend.id},
		)
		assert response.status_code == 409
		assert db_session.scalar(select(func.count(Application.id))) == 1
	finally:
		app.dependency_overrides.clear()


def test_cors_preflight_allows_configured_widget_origin_only() -> None:
	allowed_origin = "https://apply.example.org"
	configured = Settings(cors_allowed_origins=allowed_origin)
	assert configured.allowed_origins == [allowed_origin]
	with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS"):
		Settings(cors_allowed_origins="https://*.example.org")
	client = TestClient(create_app(configured))

	allowed = client.options(
		"/api/v1/cohorts/widget-token/apply",
		headers={
			"Origin": allowed_origin,
			"Access-Control-Request-Method": "POST",
			"Access-Control-Request-Headers": "content-type",
		},
	)
	assert allowed.status_code == 200
	assert allowed.headers["access-control-allow-origin"] == allowed_origin
	assert "access-control-allow-credentials" not in allowed.headers

	blocked = client.options(
		"/api/v1/cohorts/widget-token/apply",
		headers={
			"Origin": "https://unapproved.example.org",
			"Access-Control-Request-Method": "POST",
			"Access-Control-Request-Headers": "content-type",
		},
	)
	assert "access-control-allow-origin" not in blocked.headers
