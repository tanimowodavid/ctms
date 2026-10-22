from app.core.database import get_db
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.models import Profile

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
	session: Session = Depends(get_db),
) -> Profile:
	unauthorized = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Invalid or expired access token",
		headers={"WWW-Authenticate": "Bearer"},
	)
	if credentials is None:
		raise unauthorized
	try:
		payload = decode_access_token(credentials.credentials)
	except InvalidTokenError as exc:
		raise unauthorized from exc
	if payload.get("type") != "access" or not isinstance(payload.get("sub"), str):
		raise unauthorized
	profile = session.get(Profile, payload["sub"])
	if profile is None or profile.status != "ACTIVE":
		raise unauthorized
	return profile


def require_roles(*roles: str) -> Callable[..., Profile]:
	def role_dependency(profile: Profile = Depends(get_current_user)) -> Profile:
		if profile.role not in roles:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
		return profile

	return role_dependency

__all__ = ["get_current_user", "get_db", "require_roles"]
