from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import create_access_token
from app.main import app
from app.models import Cohort, Conversation, Profile, Track


def add_conversation_set(session: Session, name: str, token: str) -> tuple[Cohort, Track]:
	cohort = Cohort(
		name=name,
		start_date=datetime.now(UTC) - timedelta(days=1),
		end_date=datetime.now(UTC) + timedelta(days=30),
		status="ACTIVE",
		embed_token=token,
	)
	track = Track(name="Backend")
	cohort.tracks.append(track)
	cohort.conversation = Conversation(conversation_type="GENERAL")
	track.conversation = Conversation(conversation_type="TRACK")
	session.add(cohort)
	session.flush()
	return cohort, track


def add_profile(session: Session, email: str, role: str, **values: str) -> Profile:
	profile = Profile(
		email=email,
		full_name=email.split("@")[0],
		role=role,
		status="ACTIVE",
		password_hash="test-hash",
		tag=role,
		**values,
	)
	session.add(profile)
	session.commit()
	return profile


def test_messaging_access_and_sender_identity(db_session: Session) -> None:
	cohort, track = add_conversation_set(db_session, "First", "first")
	other, _ = add_conversation_set(db_session, "Second", "second")
	db_session.commit()
	talent = add_profile(db_session, "talent@example.com", "TALENT", cohort_id=cohort.id, track_id=track.id)
	mentor = add_profile(db_session, "mentor@example.com", "MENTOR")
	general_id = cohort.conversation.id
	track_id = track.conversation.id
	other_general_id = other.conversation.id
	other_track_id = other.tracks[0].conversation.id

	def override_db():
		yield db_session

	app.dependency_overrides[get_db] = override_db
	client = TestClient(app)
	try:
		talent_headers = {"Authorization": f"Bearer {create_access_token(talent.id, talent.role)}"}
		mentor_headers = {"Authorization": f"Bearer {create_access_token(mentor.id, mentor.role)}"}
		conversations = client.get("/api/v1/conversations", headers=talent_headers)
		assert conversations.status_code == 200
		assert {item["id"] for item in conversations.json()} == {general_id, track_id}

		assert client.get(
			f"/api/v1/conversations/{other_general_id}/messages", headers=talent_headers
		).status_code == 404
		assert client.post(
			f"/api/v1/conversations/{general_id}/messages",
			headers=talent_headers,
			json={"content": "  Hello cohort  ", "userId": mentor.id},
		).status_code == 201
		message = client.get(
			f"/api/v1/conversations/{general_id}/messages?limit=10&offset=0", headers=talent_headers
		).json()[0]
		assert message["content"] == "Hello cohort"
		assert message["userId"] == talent.id
		assert message["senderName"] == talent.full_name

		staff_listing = client.get("/api/v1/conversations", headers=mentor_headers)
		assert staff_listing.status_code == 200
		assert {item["id"] for item in staff_listing.json()} == {
			general_id, track_id, other_general_id, other_track_id
		}
		assert client.post(
			f"/api/v1/conversations/{other_general_id}/messages",
			headers=mentor_headers,
			json={"content": "Staff can reach all cohorts"},
		).status_code == 201

		talent.status = "SUSPENDED"
		db_session.commit()
		assert client.get("/api/v1/conversations", headers=talent_headers).status_code == 403
		assert client.get(f"/api/v1/conversations/{general_id}/messages", headers=talent_headers).status_code == 403
		assert client.post(
			f"/api/v1/conversations/{general_id}/messages",
			headers=talent_headers,
			json={"content": "No longer allowed"},
		).status_code == 403
	finally:
		app.dependency_overrides.pop(get_db, None)
