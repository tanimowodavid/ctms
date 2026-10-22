from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PublicApplicationCreate(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	full_name: str = Field(alias="fullName", min_length=1, max_length=255)
	email: str = Field(min_length=3, max_length=320)
	track_id: str = Field(alias="trackId", min_length=1, max_length=36)

	@field_validator("full_name")
	@classmethod
	def trim_full_name(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("fullName must not be blank")
		return value

	@field_validator("email")
	@classmethod
	def normalize_email(cls, value: str) -> str:
		value = value.strip().lower()
		if not re.fullmatch(
			r"[^@\s]{1,64}@(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",
			value,
			flags=re.ASCII,
		):
			raise ValueError("email must be a valid email address")
		return value

	@field_validator("track_id")
	@classmethod
	def trim_track_id(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("trackId must not be blank")
		return value


class ApplicationSubmitted(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	message: str = "Application submitted successfully"
	application_id: str = Field(alias="applicationId")
	status: str


class PublicTrackOption(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: str
	name: str


class PublicApplicationOptions(BaseModel):
	cohort_name: str = Field(alias="cohortName")
	start_date: datetime = Field(alias="startDate")
	accepting_applications: bool = Field(alias="acceptingApplications")
	tracks: list[PublicTrackOption]
