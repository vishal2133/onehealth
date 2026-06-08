import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import create_access_token, hash_otp
from app.database import get_db
from app.models import Doctor, OTP
from app.schemas.auth import SendOTPRequest, SendOTPResponse, TokenResponse, VerifyOTPRequest
from app.schemas.doctor import DoctorProfile
from app.services.email import send_otp_email


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-otp", response_model=SendOTPResponse)
def send_otp(payload: SendOTPRequest, db: Session = Depends(get_db)) -> SendOTPResponse:
    email = payload.email.lower()
    doctor = db.scalar(select(Doctor).where(Doctor.email == email))
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No registered doctor uses this email")

    code = settings.dev_otp_code if settings.environment == "development" else f"{secrets.randbelow(1_000_000):06d}"
    db.execute(update(OTP).where(OTP.email == email, OTP.used.is_(False)).values(used=True))
    db.add(
        OTP(
            email=email,
            code_hash=hash_otp(code),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes),
        )
    )
    db.commit()
    send_otp_email(email, code)

    return SendOTPResponse(
        message="OTP sent",
        expires_in_seconds=settings.otp_expire_minutes * 60,
        dev_code=code if settings.environment == "development" else None,
    )


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower()
    otp = db.scalar(
        select(OTP)
        .where(OTP.email == email, OTP.used.is_(False))
        .order_by(OTP.created_at.desc())
    )
    now = datetime.now(timezone.utc)
    if otp is None or otp.expires_at < now or otp.code_hash != hash_otp(payload.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")

    doctor = db.scalar(select(Doctor).where(Doctor.email == email))
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor account not found")

    otp.used = True
    db.commit()
    return TokenResponse(access_token=create_access_token(doctor.id), doctor=DoctorProfile.model_validate(doctor))
