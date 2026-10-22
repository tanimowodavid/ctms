import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Cohort, Conversation, Profile, Track
from app.schemas.cohort import CohortCreate, TrackCreate


def create_cohort(session: Session, data: CohortCreate) -> Cohort:
	cohort = Cohort(
		name=data.name,
		start_date=data.start_date,
		end_date=data.end_date,
		status="ACTIVE",
		embed_token=secrets.token_urlsafe(32),
	)
	cohort.tracks = [Track(name=track.name) for track in data.tracks]
	cohort.conversation = Conversation(conversation_type="GENERAL")
	for track in cohort.tracks:
		track.conversation = Conversation(conversation_type="TRACK")
	session.add(cohort)
	session.commit()
	return session.scalar(
		select(Cohort).options(selectinload(Cohort.tracks)).where(Cohort.id == cohort.id)
	)


def list_cohorts(session: Session, actor: Profile) -> list[Cohort]:
	statement = select(Cohort).options(selectinload(Cohort.tracks)).order_by(Cohort.start_date, Cohort.id)
	if actor.role == "TALENT":
		if actor.cohort_id is None:
			return []
		statement = statement.where(Cohort.id == actor.cohort_id)
	return list(session.scalars(statement).all())


def create_track(session: Session, cohort_id: str, data: TrackCreate) -> Track | None:
	cohort = session.get(Cohort, cohort_id)
	if cohort is None:
		return None
	track = Track(name=data.name)
	track.conversation = Conversation(conversation_type="TRACK")
	cohort.tracks.append(track)
	session.commit()
	return track


def list_tracks(session: Session, cohort_id: str, actor: Profile) -> list[Track] | None:
	cohort = session.get(Cohort, cohort_id)
	if cohort is None:
		return None
	statement = select(Track).where(Track.cohort_id == cohort_id).order_by(Track.name, Track.id)
	if actor.role == "TALENT" and actor.cohort_id != cohort_id:
		return []
	return list(session.scalars(statement).all())
