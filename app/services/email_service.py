from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
import smtplib
import ssl
from urllib.parse import urlencode, urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.security import SETUP_TOKEN_EXPIRE_HOURS, generate_setup_token
from app.models import EmailOutbox, PasswordSetupToken, Profile


def _setup_url(token: str) -> str:
	parts = urlsplit(settings.setup_link_base_url)
	query = urlencode({"token": token})
	separator = "&" if parts.query else ""
	return urlunsplit((parts.scheme, parts.netloc, parts.path, f"{parts.query}{separator}{query}", parts.fragment))


def send_staff_setup_email(profile: Profile, setup_url: str) -> None:
	message = EmailMessage()
	account_kind = "talent" if profile.role == "TALENT" else profile.role.lower()
	message["Subject"] = "Complete your CTMS account setup"
	message["From"] = settings.smtp_from_email
	message["To"] = profile.email
	message.set_content(
		f"Hello {profile.full_name},\n\n"
		f"Your CTMS {account_kind} account has been created. Complete setup within "
		f"{SETUP_TOKEN_EXPIRE_HOURS} hours by opening this link:\n{setup_url}\n\n"
		"If you were not expecting this invitation, you can ignore this message."
	)

	if settings.smtp_use_ssl:
		with smtplib.SMTP_SSL(
			settings.smtp_host,
			settings.smtp_port,
			timeout=settings.smtp_timeout_seconds,
			context=ssl.create_default_context(),
		) as server:
			if settings.smtp_username and settings.smtp_password:
				server.login(settings.smtp_username, settings.smtp_password)
			server.send_message(message)
		return

	with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as server:
		server.ehlo()
		if settings.smtp_starttls:
			server.starttls(context=ssl.create_default_context())
			server.ehlo()
		if settings.smtp_username and settings.smtp_password:
			server.login(settings.smtp_username, settings.smtp_password)
		server.send_message(message)


def process_next_email(session_factory: sessionmaker | None = None) -> bool:
	"""Send one due outbox event. Returns False when no event is due."""
	if session_factory is None:
		from app.core.database import SessionLocal

		session_factory = SessionLocal

	with session_factory() as session:
		outbox = session.scalar(
			select(EmailOutbox)
			.where(EmailOutbox.status == "PENDING", EmailOutbox.next_attempt_at <= datetime.now(UTC))
			.order_by(EmailOutbox.created_at)
			.with_for_update(skip_locked=True)
			.limit(1)
		)
		if outbox is None:
			return False

		profile = session.get(Profile, outbox.profile_id)
		if profile is None or profile.status != "INACTIVE":
			outbox.status = "SENT"
			outbox.last_error = "Skipped: associated profile is unavailable or already active"
			session.commit()
			return True

		plain_token, token_hash = generate_setup_token()
		expires_at = datetime.now(UTC) + timedelta(hours=SETUP_TOKEN_EXPIRE_HOURS)
		token_record = session.scalar(
			select(PasswordSetupToken).where(PasswordSetupToken.profile_id == profile.id).with_for_update()
		)
		if token_record is None:
			token_record = PasswordSetupToken(
				profile_id=profile.id,
				token_hash=token_hash,
				expires_at=expires_at,
			)
			session.add(token_record)
		else:
			token_record.token_hash = token_hash
			token_record.expires_at = expires_at
			token_record.used_at = None

		try:
			send_staff_setup_email(profile, _setup_url(plain_token))
		except Exception as exc:  # SMTP/network errors must leave the durable event retryable.
			outbox.attempts += 1
			backoff = min(
				settings.worker_retry_base_seconds * (2 ** min(outbox.attempts - 1, 20)),
				settings.worker_retry_max_seconds,
			)
			outbox.next_attempt_at = datetime.now(UTC) + timedelta(seconds=backoff)
			outbox.last_error = f"{type(exc).__name__}: {exc}"[:1000]
		else:
			outbox.status = "SENT"
			outbox.attempts += 1
			outbox.sent_at = datetime.now(UTC)
			outbox.last_error = None
		session.commit()
	return True
