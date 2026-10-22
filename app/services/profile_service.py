from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import EmailOutbox, Profile
from app.schemas.profile import StaffProfileCreate


class ProfileAlreadyExists(Exception):
	pass


class StaffRoleNotAllowed(Exception):
	pass


def create_staff_profile(session: Session, actor: Profile, data: StaffProfileCreate) -> Profile:
	allowed_roles = {"ADMIN": {"MENTOR"}, "SUPER_ADMIN": {"ADMIN"}}
	if data.role not in allowed_roles.get(actor.role, set()):
		raise StaffRoleNotAllowed

	email = data.email.strip().lower()
	duplicate = session.scalar(select(Profile.id).where(func.lower(func.trim(Profile.email)) == email).limit(1))
	if duplicate:
		raise ProfileAlreadyExists

	profile = Profile(
		email=email,
		full_name=data.full_name.strip(),
		bio=data.bio,
		role=data.role,
		status="INACTIVE",
		tag=data.role,
	)
	session.add(profile)
	session.flush()
	session.add(EmailOutbox(profile_id=profile.id, event_type="STAFF_PASSWORD_SETUP"))
	try:
		session.commit()
	except IntegrityError as exc:
		session.rollback()
		if "uq_profile_email_normalized" in str(exc.orig) or "uq_profile_email" in str(exc.orig):
			raise ProfileAlreadyExists from exc
		raise
	session.refresh(profile)
	return profile
