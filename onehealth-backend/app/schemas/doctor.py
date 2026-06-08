from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from app.schemas.base import APIModel


class DoctorProfile(APIModel):
    id: int
    name: str
    email: str
    specialty: str
    department: str | None
    phone: str | None
    qualifications: str | None
    reg_number: str | None
    experience: str | None
    hospital: str | None
    photo_url: str | None
    created_at: datetime


class AvailabilityDay(APIModel):
    active: bool
    start: str = Field(pattern=r"^\d{2}:\d{2}$")
    end: str = Field(pattern=r"^\d{2}:\d{2}$")

    @model_validator(mode="after")
    def validate_range(self) -> "AvailabilityDay":
        if self.active and self.start >= self.end:
            raise ValueError("end time must be after start time")
        return self


class WeeklyAvailabilityUpdate(APIModel):
    schedule: dict[str, AvailabilityDay]


class DateAvailabilityUpdate(APIModel):
    availability: dict[str, Any]


class AvailabilityResponse(APIModel):
    weekly: dict[str, Any]
    dates: dict[str, Any]


class PhotoResponse(APIModel):
    photo_url: str
