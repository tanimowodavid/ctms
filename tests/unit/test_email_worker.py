from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_setup_token
from app.models import EmailOutbox, PasswordSetupToken, Profile
from app.services import email_service


def make_pending_email(session: Session) -> tuple[Profile, EmailOutbox]:
	profile = Profile(email="mentor@example.com", full_name="Morgan Mentor", role="MENTOR", status="INACTIVE", tag="MENTOR")
	session.add(profile)
	session.flush()
	outbox = EmailOutbox(profile_id=profile.id, event_type="STAFF_PASSWORD_SETUP")
	session.add(outbox)
	session.commit()
	return profile, outbox


def test_worker_sends_setup_email_and_marks_outbox_sent(engine, db_session: Session, monkeypatch) -> None:
	profile, outbox = make_pending_email(db_session)
	delivered: list[tuple[str, str]] = []
	monkeypatch.setattr(email_service, "send_staff_setup_email", lambda recipient, link: delivered.append((recipient.email, link)))
	factory = sessionmaker(bind=engine, expire_on_commit=False)

	assert email_service.process_next_email(factory)
	db_session.refresh(outbox)
	assert delivered[0][0] == profile.email
	token = parse_qs(urlsplit(delivered[0][1]).query)["token"][0]
	assert outbox.status == "SENT"
	assert outbox.attempts == 1
	token_record = db_session.scalar(select(PasswordSetupToken).where(PasswordSetupToken.profile_id == profile.id))
	assert token_record is not None
	assert token_record.token_hash == hash_setup_token(token)
	assert token_record.token_hash != token


def test_worker_retries_failure_with_exponential_backoff(engine, db_session: Session, monkeypatch) -> None:
	_, outbox = make_pending_email(db_session)
	monkeypatch.setattr(email_service, "send_staff_setup_email", lambda *_: (_ for _ in ()).throw(ConnectionError("offline")))
	monkeypatch.setattr(email_service.settings, "worker_retry_base_seconds", 2)
	monkeypatch.setattr(email_service.settings, "worker_retry_max_seconds", 10)
	factory = sessionmaker(bind=engine, expire_on_commit=False)
	before = datetime.now(UTC)

	assert email_service.process_next_email(factory)
	db_session.refresh(outbox)
	assert outbox.status == "PENDING"
	assert outbox.attempts == 1
	next_attempt_at = outbox.next_attempt_at
	if next_attempt_at.tzinfo is None:
		next_attempt_at = next_attempt_at.replace(tzinfo=UTC)
	assert before + timedelta(seconds=1) < next_attempt_at <= before + timedelta(seconds=4)
	assert outbox.last_error.startswith("ConnectionError")
