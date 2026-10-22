from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import generate_setup_token, hash_password
from app.main import app
from app.models import Application, Cohort, EmailOutbox, PasswordSetupToken, Profile, Track


def add_profile(session: Session, email: str, role: str) -> Profile:
	profile = Profile(
		email=email,
		full_name=email.split("@")[0],
		password_hash=hash_password("correct-horse-battery-12"),
		role=role,
		status="ACTIVE",
		tag=role,
	)
	session.add(profile)
	session.commit()
	return profile


def add_application(session: Session, email: str = "talent@example.com") -> Application:
	cohort = Cohort(
		name="Review Cohort",
		start_date=datetime.now(UTC) - timedelta(days=1),
		end_date=datetime.now(UTC) + timedelta(days=60),
		status="ACTIVE",
		embed_token=f"review-{email}",
	)
	track = Track(name="Backend")
	cohort.tracks.append(track)
	session.add(cohort)
	session.flush()
	application = Application(
		full_name="Taylor Talent",
		email=email,
		status="PENDING",
		cohort_id=cohort.id,
		track_id=track.id,
	)
	session.add(application)
	session.commit()
	return application


def client_for(session: Session) -> TestClient:
	def override_db():
		yield session

	app.dependency_overrides[get_db] = override_db
	return TestClient(app)


def token_for(client: TestClient, email: str) -> str:
	response = client.post(
		"/api/v1/auth/login", json={"email": email, "password": "correct-horse-battery-12"}
	)
	assert response.status_code == 200
	return response.json()["accessToken"]


def test_admin_can_filter_review_approve_and_onboard_after_intake_closes(db_session: Session) -> None:
	admin = add_profile(db_session, "admin@example.com", "ADMIN")
	application = add_application(db_session)
	client = client_for(db_session)
	try:
		token = token_for(client, admin.email)
		headers = {"Authorization": f"Bearer {token}"}
		listing = client.get("/api/v1/applications?status=PENDING", headers=headers)
		assert listing.status_code == 200
		assert [item["id"] for item in listing.json()] == [application.id]
		assert client.get(f"/api/v1/applications/{application.id}", headers=headers).json()["email"] == application.email

		approved = client.post(f"/api/v1/applications/{application.id}/approve", headers=headers)
		assert approved.status_code == 201, approved.text
		profile = db_session.get(Profile, approved.json()["id"])
		assert profile.role == "TALENT"
		assert profile.status == "INACTIVE"
		assert profile.cohort_id == application.cohort_id
		assert profile.track_id == application.track_id
		assert db_session.get(Application, application.id).status == "APPROVED"
		outbox = db_session.scalar(
			select(EmailOutbox).where(
				EmailOutbox.profile_id == profile.id,
				EmailOutbox.event_type == "TALENT_PASSWORD_SETUP",
			)
		)
		assert outbox is not None and outbox.status == "PENDING"

		setup_token, token_hash = generate_setup_token()
		db_session.add(
			PasswordSetupToken(
				profile_id=profile.id,
				token_hash=token_hash,
				expires_at=datetime.now(UTC) + timedelta(hours=24),
			)
		)
		db_session.commit()
		setup = client.post(
			"/api/v1/auth/setup-password",
			json={"setupToken": setup_token, "password": "a-new-talent-password-123"},
		)
		assert setup.status_code == 204
		assert db_session.get(Profile, profile.id).status == "ACTIVE"
		login = client.post(
			"/api/v1/auth/login",
			json={"email": profile.email, "password": "a-new-talent-password-123"},
		)
		assert login.status_code == 200

		assert client.post(f"/api/v1/applications/{application.id}/approve", headers=headers).status_code == 409
		assert client.get("/api/v1/applications?status=REJECTED", headers=headers).json() == []
	finally:
		app.dependency_overrides.clear()


def test_review_is_admin_only_and_rejection_does_not_create_profile(db_session: Session) -> None:
	mentor = add_profile(db_session, "mentor@example.com", "MENTOR")
	application = add_application(db_session)
	client = client_for(db_session)
	try:
		token = token_for(client, mentor.email)
		headers = {"Authorization": f"Bearer {token}"}
		assert client.get("/api/v1/applications", headers=headers).status_code == 403
		assert client.post(f"/api/v1/applications/{application.id}/reject", headers=headers).status_code == 403

		admin = add_profile(db_session, "reviewer@example.com", "SUPER_ADMIN")
		headers = {"Authorization": f"Bearer {token_for(client, admin.email)}"}
		rejected = client.post(f"/api/v1/applications/{application.id}/reject", headers=headers)
		assert rejected.status_code == 200
		assert rejected.json()["status"] == "REJECTED"
		assert db_session.scalar(select(Profile.id).where(Profile.email == application.email)) is None
		assert db_session.scalar(select(EmailOutbox.id)) is None
		assert client.post(f"/api/v1/applications/{application.id}/reject", headers=headers).status_code == 409
	finally:
		app.dependency_overrides.clear()


def test_approval_conflicts_with_existing_profile_without_partial_changes(db_session: Session) -> None:
	admin = add_profile(db_session, "admin@example.com", "ADMIN")
	application = add_application(db_session, "Existing@example.com")
	add_profile(db_session, "existing@example.com", "MENTOR")
	client = client_for(db_session)
	try:
		headers = {"Authorization": f"Bearer {token_for(client, admin.email)}"}
		response = client.post(f"/api/v1/applications/{application.id}/approve", headers=headers)
		assert response.status_code == 409
		assert db_session.get(Application, application.id).status == "PENDING"
		assert db_session.scalar(select(EmailOutbox.id)) is None
	finally:
		app.dependency_overrides.clear()
