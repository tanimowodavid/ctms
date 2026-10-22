from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import Profile
from app.schemas.profile import ProfileResponse, StaffProfileCreate
from app.services.profile_service import ProfileAlreadyExists, StaffRoleNotAllowed, create_staff_profile

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/staff", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
	payload: StaffProfileCreate,
	actor: Profile = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> Profile:
	try:
		return create_staff_profile(session, actor, payload)
	except StaffRoleNotAllowed as exc:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may not create this staff role") from exc
	except ProfileAlreadyExists as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A profile with this email already exists") from exc
	except IntegrityError as exc:
		session.rollback()
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unable to create profile") from exc
