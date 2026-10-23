from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import Message, Profile
from app.schemas.messaging import ConversationResponse, MessageCreate, MessageResponse
from app.services.chat_service import (
	create_message,
	get_accessible_conversation,
	list_accessible_conversations,
	list_messages,
)

router = APIRouter(prefix="/conversations", tags=["messaging"])


def response_for(message: Message) -> MessageResponse:
	return MessageResponse(
		id=message.id,
		conversationId=message.conversation_id,
		userId=message.user_id,
		content=message.content,
		createdAt=message.created_at,
		senderName=message.user.full_name,
		senderRole=message.user.role,
	)


@router.get("", response_model=list[ConversationResponse])
def get_conversations(
	actor: Profile = Depends(get_current_user), session: Session = Depends(get_db)
) -> list[ConversationResponse]:
	return [ConversationResponse.model_validate(item) for item in list_accessible_conversations(session, actor)]


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
	conversation_id: str,
	limit: int = Query(default=50, ge=1, le=100),
	offset: int = Query(default=0, ge=0),
	actor: Profile = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> list[MessageResponse]:
	if get_accessible_conversation(session, conversation_id, actor) is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
	return [response_for(item) for item in list_messages(session, conversation_id, limit, offset)]


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def post_message(
	conversation_id: str,
	payload: MessageCreate,
	actor: Profile = Depends(get_current_user),
	session: Session = Depends(get_db),
) -> MessageResponse:
	if get_accessible_conversation(session, conversation_id, actor) is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
	return response_for(create_message(session, conversation_id, actor, payload.content))
