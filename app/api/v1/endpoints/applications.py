from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.application import ApplicationSubmitted, PublicApplicationCreate, PublicApplicationOptions
from app.services.application_service import (
	ApplicationIntakeClosed,
	ApplicationTrackNotFound,
	CohortEmbedTokenNotFound,
	DuplicateApplication,
	get_public_application_options,
	submit_application,
)

router = APIRouter(prefix="/cohorts", tags=["public applications"])


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
