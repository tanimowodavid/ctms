from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, hash_setup_token, verify_password
from app.models import PasswordSetupToken, Profile


def authenticate_profile(session: Session, email: str, password: str) -> Profile | None:
	profile = session.scalar(select(Profile).where(func.lower(func.trim(Profile.email)) == email.strip().lower()))
	if profile is None or profile.status != "ACTIVE" or not profile.password_hash:
		return None
	if not verify_password(password, profile.password_hash):
		return None
	return profile


def complete_password_setup(session: Session, token: str, password: str) -> bool:
	token_record = session.scalar(
		select(PasswordSetupToken)
		.where(PasswordSetupToken.token_hash == hash_setup_token(token))
		.with_for_update()
	)
	if token_record is None or token_record.used_at is not None:
		return False

	now = datetime.now(UTC)
	expires_at = token_record.expires_at
	if expires_at.tzinfo is None:
		expires_at = expires_at.replace(tzinfo=UTC)
	if expires_at <= now:
		return False

	profile = session.get(Profile, token_record.profile_id)
	if profile is None or profile.status != "INACTIVE":
		return False
	profile.password_hash = hash_password(password)
	profile.status = "ACTIVE"
	token_record.used_at = now
	session.commit()
	return True
