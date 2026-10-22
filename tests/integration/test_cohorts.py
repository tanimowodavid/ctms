from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Cohort, Conversation, Profile, Track
from app.services import cohort_service


def add_profile(
	session: Session, email: str, role: str, cohort_id: str | None = None, track_id: str | None = None
) -> Profile:
	profile = Profile(
		email=email,
		full_name=role.title(),
		password_hash=hash_password("test-password-12345"),
		role=role,
		status="ACTIVE",
		tag=role,
		cohort_id=cohort_id,
		track_id=track_id,
	)
	session.add(profile)
	session.commit()
	return profile


def authorized(profile: Profile) -> dict[str, str]:
	return {"Authorization": f"Bearer {create_access_token(profile.id, profile.role)}"}


def client_for(session: Session) -> TestClient:
	def override_db():
		yield session

	app.dependency_overrides[get_db] = override_db
	return TestClient(app)


def cohort_payload(name: str = "Fall 2026") -> dict:
	return {
		"name": name,
		"startDate": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
		"endDate": (datetime.now(UTC) + timedelta(days=90)).isoformat(),
		"tracks": [{"name": "Backend"}, {"name": "Frontend"}],
	}


def test_admin_creates_cohort_and_tracks_with_conversations_and_can_add_track(db_session: Session) -> None:
	admin = add_profile(db_session, "admin@example.com", "ADMIN")
	client = client_for(db_session)
	try:
		response = client.post("/api/v1/cohorts", headers=authorized(admin), json=cohort_payload())
		assert response.status_code == 201, response.text
		cohort = response.json()
		assert cohort["embedToken"] and cohort["name"] == "Fall 2026"
		assert {track["name"] for track in cohort["tracks"]} == {"Backend", "Frontend"}
		assert db_session.scalar(
			select(func.count(Conversation.id)).where(Conversation.cohort_id == cohort["id"])
		) == 1
		assert db_session.scalar(select(func.count(Conversation.id)).where(Conversation.track_id.is_not(None))) == 2

		added = client.post(
			f"/api/v1/cohorts/{cohort['id']}/tracks",
			headers=authorized(admin),
			json={"name": "Data Science"},
		)
		assert added.status_code == 201, added.text
		assert added.json()["name"] == "Data Science"
		assert added.json()["cohortId"] == cohort["id"]
		assert db_session.scalar(select(Conversation.id).where(Conversation.track_id == added.json()["id"]))
	finally:
		app.dependency_overrides.clear()


def test_cohort_and_track_creation_permissions_and_talent_listing_scope(db_session: Session) -> None:
	admin = add_profile(db_session, "admin@example.com", "ADMIN")
	mentor = add_profile(db_session, "mentor@example.com", "MENTOR")
	client = client_for(db_session)
	try:
		created = client.post("/api/v1/cohorts", headers=authorized(admin), json=cohort_payload())
		assert created.status_code == 201, created.text
		cohort_id = created.json()["id"]
		track_id = created.json()["tracks"][0]["id"]
		talent = add_profile(db_session, "talent@example.com", "TALENT", cohort_id, track_id)

		assert client.post("/api/v1/cohorts", headers=authorized(mentor), json=cohort_payload("Denied")).status_code == 403
		assert client.post(
			f"/api/v1/cohorts/{cohort_id}/tracks", headers=authorized(mentor), json={"name": "Denied"}
		).status_code == 403
		assert [item["id"] for item in client.get("/api/v1/cohorts", headers=authorized(talent)).json()] == [cohort_id]
		assert len(client.get(f"/api/v1/cohorts/{cohort_id}/tracks", headers=authorized(talent)).json()) == 2
		assert client.get("/api/v1/cohorts/other-cohort/tracks", headers=authorized(talent)).status_code == 403

		before = db_session.scalar(select(func.count(Cohort.id)))
		invalid = client.post(
			"/api/v1/cohorts", headers=authorized(admin), json={**cohort_payload("Invalid"), "tracks": []}
		)
		assert invalid.status_code == 422
		assert db_session.scalar(select(func.count(Cohort.id))) == before
	finally:
		app.dependency_overrides.clear()


def test_failed_cohort_insert_rolls_back_tracks_and_conversations(db_session: Session, monkeypatch) -> None:
	admin = add_profile(db_session, "admin@example.com", "ADMIN")
	client = client_for(db_session)
	try:
		first = client.post("/api/v1/cohorts", headers=authorized(admin), json=cohort_payload("First"))
		assert first.status_code == 201, first.text
		before = (
			db_session.scalar(select(func.count(Cohort.id))),
			db_session.scalar(select(func.count(Track.id))),
			db_session.scalar(select(func.count(Conversation.id))),
		)
		monkeypatch.setattr(cohort_service.secrets, "token_urlsafe", lambda _: first.json()["embedToken"])
		failing_client = TestClient(app, raise_server_exceptions=False)
		response = failing_client.post(
			"/api/v1/cohorts", headers=authorized(admin), json=cohort_payload("Duplicate token")
		)
		assert response.status_code == 500
		db_session.rollback()
		after = (
			db_session.scalar(select(func.count(Cohort.id))),
			db_session.scalar(select(func.count(Track.id))),
			db_session.scalar(select(func.count(Conversation.id))),
		)
		assert after == before
	finally:
		app.dependency_overrides.clear()
