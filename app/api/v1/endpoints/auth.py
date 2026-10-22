from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, LoginResponse, PasswordSetupRequest
from app.services.auth_service import authenticate_profile, complete_password_setup

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db)) -> LoginResponse:
	profile = authenticate_profile(session, payload.email, payload.password)
	if profile is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
	return LoginResponse(
		accessToken=create_access_token(profile.id, profile.role),
		user={"id": profile.id, "email": profile.email, "fullName": profile.full_name, "role": profile.role},
	)


@router.post("/setup-password", status_code=status.HTTP_204_NO_CONTENT)
def setup_password(payload: PasswordSetupRequest, session: Session = Depends(get_db)) -> Response:
	if not complete_password_setup(session, payload.setup_token, payload.password):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired setup token")
	return Response(status_code=status.HTTP_204_NO_CONTENT)
