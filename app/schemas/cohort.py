from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TrackCreate(BaseModel):
	name: str = Field(min_length=1, max_length=255)

	@field_validator("name")
	@classmethod
	def trim_name(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("must not be blank")
		return value


class CohortCreate(BaseModel):
	name: str = Field(min_length=1, max_length=255)
	start_date: datetime = Field(alias="startDate")
	end_date: datetime = Field(alias="endDate")
	tracks: list[TrackCreate] = Field(min_length=1)

	@field_validator("name")
	@classmethod
	def trim_name(cls, value: str) -> str:
		value = value.strip()
		if not value:
			raise ValueError("must not be blank")
		return value

	@model_validator(mode="after")
	def validate_dates(self) -> "CohortCreate":
		if self.start_date.utcoffset() is None or self.end_date.utcoffset() is None:
			raise ValueError("startDate and endDate must include a timezone")
		if self.end_date <= self.start_date:
			raise ValueError("endDate must be after startDate")
		return self


class TrackResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True, populate_by_name=True)

	id: str
	name: str
	cohort_id: str = Field(alias="cohortId")


class CohortResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True, populate_by_name=True)

	id: str
	name: str
	start_date: datetime = Field(alias="startDate")
	end_date: datetime = Field(alias="endDate")
	status: str
	embed_token: str = Field(alias="embedToken")
	tracks: list[TrackResponse]
