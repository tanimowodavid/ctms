from datetime import UTC, datetime, timedelta
import hashlib
import secrets
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 15
SETUP_TOKEN_EXPIRE_HOURS = 24


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
	return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
	return password_context.verify(password, password_hash)


def create_access_token(profile_id: str, role: str) -> str:
	expires_at = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	return jwt.encode(
		{"sub": profile_id, "role": role, "type": "access", "exp": expires_at},
		settings.jwt_secret,
		algorithm="HS256",
	)


def decode_access_token(token: str) -> dict[str, Any]:
	return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def generate_setup_token() -> tuple[str, str]:
	plain_token = secrets.token_urlsafe(32)
	token_hash = hashlib.sha256(plain_token.encode("utf-8")).hexdigest()
	return plain_token, token_hash


def hash_setup_token(token: str) -> str:
	return hashlib.sha256(token.encode("utf-8")).hexdigest()
