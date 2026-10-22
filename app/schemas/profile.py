from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StaffProfileCreate(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	full_name: str = Field(alias="fullName", min_length=1, max_length=255)
	email: str = Field(max_length=320)
	role: Literal["ADMIN", "MENTOR"]
	bio: str | None = None

	@field_validator("full_name", "email")
	@classmethod
	def trim_required_text(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("must not be blank")
		return value

	@field_validator("email")
	@classmethod
	def normalize_email(cls, value: str) -> str:
		value = value.strip().lower()
		if "@" not in value or value.startswith("@") or value.endswith("@"):
			raise ValueError("must be a valid email address")
		return value

	@field_validator("bio")
	@classmethod
	def trim_bio(cls, value: str | None) -> str | None:
		return value.strip() or None if value is not None else None


class ProfileResponse(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	id: str
	email: str
	full_name: str = Field(alias="fullName")
	role: str
	status: str
	tag: str | None
