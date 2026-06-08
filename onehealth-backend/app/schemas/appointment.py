from datetime import date, time

from app.schemas.base import APIModel


class AppointmentResponse(APIModel):
    id: int
    date: date
    time: time
    patient_id: int
    patient_name: str
    age: int | None
    gender: str | None
    category: str
    reason: str
    status: str
    is_today: bool
