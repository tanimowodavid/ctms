from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import generate_setup_token, hash_password, hash_setup_token
from app.main import app
from app.models import EmailOutbox, PasswordSetupToken, Profile


def add_profile(session: Session, *, email: str, role: str, status: str = "ACTIVE") -> Profile:
	profile = Profile(
		email=email,
		full_name=email.split("@")[0].title(),
		password_hash=hash_password("correct-horse-battery-12") if status == "ACTIVE" else None,
		role=role,
		status=status,
		tag=role,
	)
	session.add(profile)
	session.commit()
	return profile


def make_client(session: Session) -> TestClient:
	def override_db():
		yield session

	app.dependency_overrides[get_db] = override_db
	return TestClient(app)


def login(client: TestClient, email: str) -> str:
	response = client.post("/api/v1/auth/login", json={"email": email, "password": "correct-horse-battery-12"})
	assert response.status_code == 200
	return response.json()["accessToken"]


def test_staff_creation_enforces_role_permissions_and_queues_email(db_session: Session) -> None:
	admin = add_profile(db_session, email="admin@example.com", role="ADMIN")
	super_admin = add_profile(db_session, email="super@example.com", role="SUPER_ADMIN")
	add_profile(db_session, email="inactive@example.com", role="ADMIN", status="INACTIVE")
	client = make_client(db_session)
	try:
		admin_token = login(client, admin.email)
		super_token = login(client, super_admin.email)

		response = client.post(
			"/api/v1/profiles/staff",
			headers={"Authorization": f"Bearer {admin_token}"},
			json={"fullName": "Morgan Mentor", "email": " Morgan@Example.com ", "role": "MENTOR", "bio": "Coach"},
		)
		assert response.status_code == 201
		created = response.json()
		assert created["email"] == "morgan@example.com"
		assert created["role"] == created["tag"] == "MENTOR"
		assert created["status"] == "INACTIVE"
		assert db_session.scalar(select(EmailOutbox).where(EmailOutbox.profile_id == created["id"])) is not None

		forbidden = client.post(
			"/api/v1/profiles/staff",
			headers={"Authorization": f"Bearer {admin_token}"},
			json={"fullName": "Another Admin", "email": "another@example.com", "role": "ADMIN"},
		)
		assert forbidden.status_code == 403

		created_admin = client.post(
			"/api/v1/profiles/staff",
			headers={"Authorization": f"Bearer {super_token}"},
			json={"fullName": "New Admin", "email": "new-admin@example.com", "role": "ADMIN"},
		)
		assert created_admin.status_code == 201

		duplicate = client.post(
			"/api/v1/profiles/staff",
			headers={"Authorization": f"Bearer {admin_token}"},
			json={"fullName": "Morgan Again", "email": "MORGAN@example.com", "role": "MENTOR"},
		)
		assert duplicate.status_code == 409

		inactive_login = client.post(
			"/api/v1/auth/login", json={"email": "inactive@example.com", "password": "correct-horse-battery-12"}
		)
		assert inactive_login.status_code == 401
		assert client.post("/api/v1/profiles/staff", json={}).status_code == 401
	finally:
		app.dependency_overrides.clear()


def test_password_setup_activates_profile_once(db_session: Session) -> None:
	profile = add_profile(db_session, email="new-mentor@example.com", role="MENTOR", status="INACTIVE")
	plain_token, token_hash = generate_setup_token()
	db_session.add(
		PasswordSetupToken(
			profile_id=profile.id,
			token_hash=token_hash,
			expires_at=datetime.now(UTC) + timedelta(hours=1),
		)
	)
	db_session.commit()
	client = make_client(db_session)
	try:
		response = client.post(
			"/api/v1/auth/setup-password",
			json={"setupToken": plain_token, "password": "a-new-long-password-123"},
		)
		assert response.status_code == 204
		assert db_session.get(Profile, profile.id).status == "ACTIVE"
		token_record = db_session.scalar(select(PasswordSetupToken).where(PasswordSetupToken.profile_id == profile.id))
		assert token_record.token_hash == hash_setup_token(plain_token)
		assert token_record.used_at is not None
		assert client.post(
			"/api/v1/auth/setup-password",
			json={"setupToken": plain_token, "password": "a-new-long-password-123"},
		).status_code == 400
		assert client.post(
			"/api/v1/auth/login",
			json={"email": profile.email, "password": "a-new-long-password-123"},
		).status_code == 200
	finally:
		app.dependency_overrides.clear()
