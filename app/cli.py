"""Administrative commands for the CTMS application."""

import argparse
from datetime import UTC, datetime, timedelta
from getpass import getpass
import secrets

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Cohort, Conversation, Profile, Track


def bootstrap_super_admin() -> int:
	with SessionLocal() as session:
		session.execute(text("SELECT pg_advisory_xact_lock(719438210)"))
		existing = session.scalar(select(Profile.id).where(Profile.role == "SUPER_ADMIN").limit(1))
		if existing is not None:
			print("A Super Admin already exists; refusing to bootstrap another.")
			return 1

		email = input("Super Admin email: ").strip().lower()
		full_name = input("Full name: ").strip()
		password = getpass("Password (12+ characters): ")
		confirmation = getpass("Confirm password: ")
		if not email or "@" not in email or not full_name:
			print("A valid email and full name are required.")
			return 2
		if len(password) < 12 or password != confirmation:
			print("Passwords must match and contain at least 12 characters.")
			return 2

		session.add(
			Profile(
				email=email,
				full_name=full_name,
				password_hash=hash_password(password),
				role="SUPER_ADMIN",
				status="ACTIVE",
			)
		)
		session.commit()
	print(f"Bootstrapped Super Admin: {email}")
	return 0


def seed_demo() -> int:
	"""Create local Postman demo data in a completely empty application database."""
	password = getpass("Shared demo password (12+ characters): ")
	confirmation = getpass("Confirm demo password: ")
	if len(password) < 12 or password != confirmation:
		print("Passwords must match and contain at least 12 characters.")
		return 2

	with SessionLocal() as session:
		session.execute(text("SELECT pg_advisory_xact_lock(719438210)"))
		if session.scalar(select(Profile.id).limit(1)) or session.scalar(select(Cohort.id).limit(1)):
			print("The demo seed requires an empty database; no records were changed.")
			return 1

		now = datetime.now(UTC).replace(microsecond=0)
		cohort = Cohort(
			name="CTMS Demo Cohort 2027",
			start_date=now + timedelta(days=30),
			end_date=now + timedelta(days=120),
			status="ACTIVE",
			embed_token=secrets.token_urlsafe(32),
		)
		cohort.tracks = [
			Track(name=name)
			for name in (
				"Backend Engineering",
				"Frontend Engineering",
				"Data Science and AI",
				"Cloud and DevOps",
				"Cybersecurity",
			)
		]
		cohort.conversation = Conversation(conversation_type="GENERAL")
		for track in cohort.tracks:
			track.conversation = Conversation(conversation_type="TRACK")

		password_hash = hash_password(password)
		for email, full_name, role in (
			("superadmin@ctms.local", "Alex Super Admin", "SUPER_ADMIN"),
			("admin@ctms.local", "Avery Program Admin", "ADMIN"),
			("mentor1@ctms.local", "Morgan Mentor", "MENTOR"),
			("mentor2@ctms.local", "Jordan Mentor", "MENTOR"),
		):
			session.add(
				Profile(
					email=email,
					full_name=full_name,
					password_hash=password_hash,
					role=role,
					status="ACTIVE",
					tag=role,
				)
			)
		session.add(cohort)
		try:
			session.commit()
		except IntegrityError:
			session.rollback()
			print("The demo seed could not be created; no partial records were kept.")
			return 1

	print("Created the demo cohort, five tracks, and four active demo profiles.")
	print("All demo profiles use the password you entered.")
	print("This seed is for local development only; do not use it outside a disposable local database.")
	return 0


def main() -> int:
	parser = argparse.ArgumentParser(prog="ctms")
	parser.add_argument("command", choices=["bootstrap-super-admin", "seed-demo"])
	args = parser.parse_args()
	if args.command == "seed-demo":
		return seed_demo()
	return bootstrap_super_admin()


if __name__ == "__main__":
	raise SystemExit(main())
