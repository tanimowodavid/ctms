from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import Profile
from app.schemas.application import (
	ApplicationResponse,
	ApplicationSubmitted,
	PublicApplicationCreate,
	PublicApplicationOptions,
)
from app.schemas.profile import ProfileResponse
from app.services.application_service import (
	ApplicationAlreadyProcessed,
	ApplicationIntakeClosed,
	ApplicationNotFound,
	ApplicationProfileConflict,
	ApplicationTrackNotFound,
	CohortEmbedTokenNotFound,
	DuplicateApplication,
	approve_application,
	get_application,
	get_public_application_options,
	list_applications,
	reject_application,
	submit_application,
)

router = APIRouter(prefix="/cohorts", tags=["public applications"])
admin_router = APIRouter(prefix="/applications", tags=["applications"])


@admin_router.get("", response_model=list[ApplicationResponse])
def get_applications(
	cohort_id: str | None = Query(default=None, alias="cohortId", min_length=1, max_length=36),
	application_status: Literal["PENDING", "APPROVED", "REJECTED"] | None = Query(default=None, alias="status"),
	_session: Session = Depends(get_db),
	_actor: Profile = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
) -> list[ApplicationResponse]:
	return list_applications(_session, cohort_id=cohort_id, status=application_status)


@admin_router.get("/{application_id}", response_model=ApplicationResponse)
def get_application_detail(
	application_id: str,
	session: Session = Depends(get_db),
	_actor: Profile = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
) -> ApplicationResponse:
	try:
		return get_application(session, application_id)
	except ApplicationNotFound as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found") from exc


@admin_router.post("/{application_id}/approve", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def post_application_approval(
	application_id: str,
	session: Session = Depends(get_db),
	_actor: Profile = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
) -> ProfileResponse:
	try:
		_, profile = approve_application(session, application_id)
	except ApplicationNotFound as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found") from exc
	except ApplicationAlreadyProcessed as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application is no longer pending") from exc
	except ApplicationProfileConflict as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A profile with this email already exists") from exc
	return ProfileResponse.model_validate(profile)


@admin_router.post("/{application_id}/reject", response_model=ApplicationResponse)
def post_application_rejection(
	application_id: str,
	session: Session = Depends(get_db),
	_actor: Profile = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
) -> ApplicationResponse:
	try:
		return reject_application(session, application_id)
	except ApplicationNotFound as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found") from exc
	except ApplicationAlreadyProcessed as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application is no longer pending") from exc


@router.get("/{embed_token}/application-tracks", response_model=PublicApplicationOptions)
def get_application_tracks(embed_token: str, session: Session = Depends(get_db)) -> PublicApplicationOptions:
	try:
		cohort, tracks, accepting = get_public_application_options(session, embed_token)
	except CohortEmbedTokenNotFound as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid cohort embed token") from exc
	return PublicApplicationOptions(
		cohortName=cohort.name,
		startDate=cohort.start_date,
		acceptingApplications=accepting,
		tracks=tracks,
	)


@router.post("/{embed_token}/apply", response_model=ApplicationSubmitted, status_code=status.HTTP_201_CREATED)
def post_application(
	embed_token: str,
	payload: PublicApplicationCreate,
	session: Session = Depends(get_db),
) -> ApplicationSubmitted:
	try:
		application = submit_application(session, embed_token, payload)
	except CohortEmbedTokenNotFound as exc:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid cohort embed token") from exc
	except ApplicationIntakeClosed as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cohort application intake is closed") from exc
	except ApplicationTrackNotFound as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Track does not belong to this cohort") from exc
	except DuplicateApplication as exc:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An application already exists for this email") from exc
	return ApplicationSubmitted(applicationId=application.id, status=application.status)
