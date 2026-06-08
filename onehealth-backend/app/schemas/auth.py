from pydantic import EmailStr, Field

from app.schemas.base import APIModel
from app.schemas.doctor import DoctorProfile


class SendOTPRequest(APIModel):
    email: EmailStr


class SendOTPResponse(APIModel):
    message: str
    expires_in_seconds: int
    dev_code: str | None = None


class VerifyOTPRequest(APIModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    doctor: DoctorProfile
