"""Administrative commands for the CTMS application."""

import argparse
from getpass import getpass

from sqlalchemy import select, text

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Profile


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


def main() -> int:
	parser = argparse.ArgumentParser(prog="ctms")
	parser.add_argument("command", choices=["bootstrap-super-admin"])
	parser.parse_args()
	return bootstrap_super_admin()


if __name__ == "__main__":
	raise SystemExit(main())
