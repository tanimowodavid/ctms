from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Conversation, Message, Profile


def list_accessible_conversations(session: Session, actor: Profile) -> list[Conversation]:
	statement = select(Conversation).options(joinedload(Conversation.track)).order_by(
		Conversation.conversation_type, Conversation.cohort_id, Conversation.track_id, Conversation.id
	)
	if actor.role == "TALENT":
		statement = statement.where(
			(Conversation.conversation_type == "GENERAL") & (Conversation.cohort_id == actor.cohort_id)
			| (Conversation.conversation_type == "TRACK") & (Conversation.track_id == actor.track_id)
		)
	return list(session.scalars(statement).unique().all())


def get_accessible_conversation(session: Session, conversation_id: str, actor: Profile) -> Conversation | None:
	statement = select(Conversation).options(joinedload(Conversation.track)).where(Conversation.id == conversation_id)
	if actor.role == "TALENT":
		statement = statement.where(
			(Conversation.conversation_type == "GENERAL") & (Conversation.cohort_id == actor.cohort_id)
			| (Conversation.conversation_type == "TRACK") & (Conversation.track_id == actor.track_id)
		)
	return session.scalar(statement)


def list_messages(session: Session, conversation_id: str, limit: int, offset: int) -> list[Message]:
	statement = (
		select(Message)
		.options(joinedload(Message.user))
		.where(Message.conversation_id == conversation_id)
		.order_by(Message.created_at, Message.id)
		.limit(limit)
		.offset(offset)
	)
	return list(session.scalars(statement).unique().all())


def create_message(session: Session, conversation_id: str, actor: Profile, content: str) -> Message:
	message = Message(conversation_id=conversation_id, user_id=actor.id, content=content)
	session.add(message)
	session.commit()
	session.refresh(message)
	return session.scalar(select(Message).options(joinedload(Message.user)).where(Message.id == message.id))
