from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models import Cohort, Profile, Track
from app.schemas.cohort import CohortCreate, CohortResponse, TrackCreate, TrackResponse
from app.services.cohort_service import create_cohort, create_track, list_cohorts, list_tracks

router = APIRouter(prefix="/cohorts", tags=["cohorts"])


@router.post("", response_model=CohortResponse, status_code=status.HTTP_201_CREATED)
def post_cohort(
	payload: CohortCreate,
	_: Profile = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
	session: Session = Depends(get_db),
) -> Cohort:
	return create_cohort(session, payload)


@router.get("", response_model=list[CohortResponse])
def get_cohorts(
	actor: Profile = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> list[Cohort]:
	if actor.role not in {"SUPER_ADMIN", "ADMIN", "MENTOR", "TALENT"}:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
	return list_cohorts(session, actor)


@router.post("/{cohort_id}/tracks", response_model=TrackResponse, status_code=status.HTTP_201_CREATED)
def post_track(
	cohort_id: str,
	payload: TrackCreate,
	_: Profile = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
	session: Session = Depends(get_db),
) -> Track:
	track = create_track(session, cohort_id, payload)
	if track is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")
	return track


@router.get("/{cohort_id}/tracks", response_model=list[TrackResponse])
def get_tracks(
	cohort_id: str,
	actor: Profile = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> list[Track]:
	if actor.role not in {"SUPER_ADMIN", "ADMIN", "MENTOR", "TALENT"}:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
	if actor.role == "TALENT" and actor.cohort_id != cohort_id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only view tracks in your cohort")
	tracks = list_tracks(session, cohort_id, actor)
	if tracks is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohort not found")
	return tracks
