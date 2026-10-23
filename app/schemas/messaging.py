from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConversationResponse(BaseModel):
	model_config = ConfigDict(populate_by_name=True, from_attributes=True)

	id: str
	conversation_type: str = Field(alias="type")
	cohort_id: str | None = Field(alias="cohortId")
	track_id: str | None = Field(alias="trackId")


class MessageCreate(BaseModel):
	content: str = Field(min_length=1, max_length=10000)

	@field_validator("content")
	@classmethod
	def validate_content(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("content must not be blank")
		return value


class MessageResponse(BaseModel):
	model_config = ConfigDict(populate_by_name=True, from_attributes=True)

	id: str
	conversation_id: str = Field(alias="conversationId")
	user_id: str = Field(alias="userId")
	content: str
	created_at: datetime = Field(alias="createdAt")
	sender_name: str = Field(alias="senderName")
	sender_role: str = Field(alias="senderRole")
