from app.schemas.base import APIModel


class PatientResponse(APIModel):
    id: int
    name: str
    email: str | None
    phone: str | None
    age: int | None
    gender: str | None
    service: str
