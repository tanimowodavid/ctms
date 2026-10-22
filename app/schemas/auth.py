from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	email: str
	password: str

	@field_validator("email")
	@classmethod
	def normalize_email(cls, value: str) -> str:
		return value.strip().lower()


class AuthenticatedUser(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	id: str
	email: str
	full_name: str = Field(alias="fullName")
	role: str


class LoginResponse(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	access_token: str = Field(alias="accessToken")
	token_type: str = Field(default="bearer", alias="tokenType")
	user: AuthenticatedUser


class PasswordSetupRequest(BaseModel):
	setup_token: str = Field(alias="setupToken")
	password: Annotated[str, Field(min_length=12, max_length=128)]
