import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_doctor
from app.database import get_db
from app.models import Doctor
from app.schemas.doctor import (
    AvailabilityResponse,
    DateAvailabilityUpdate,
    DoctorProfile,
    PhotoResponse,
    WeeklyAvailabilityUpdate,
)


router = APIRouter(prefix="/doctors", tags=["doctors"])
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@router.get("/me", response_model=DoctorProfile)
def get_profile(doctor: Doctor = Depends(get_current_doctor)) -> Doctor:
    return doctor


@router.get("/me/availability", response_model=AvailabilityResponse)
def get_availability(doctor: Doctor = Depends(get_current_doctor)) -> AvailabilityResponse:
    return AvailabilityResponse(weekly=doctor.weekly_availability or {}, dates=doctor.date_availability or {})


@router.put("/me/availability", response_model=AvailabilityResponse)
def update_weekly_availability(
    payload: WeeklyAvailabilityUpdate,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> AvailabilityResponse:
    doctor.weekly_availability = {
        day: details.model_dump() for day, details in payload.schedule.items()
    }
    db.commit()
    return AvailabilityResponse(weekly=doctor.weekly_availability, dates=doctor.date_availability or {})


@router.put("/me/date-availability", response_model=AvailabilityResponse)
def update_date_availability(
    payload: DateAvailabilityUpdate,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> AvailabilityResponse:
    doctor.date_availability = payload.availability
    db.commit()
    return AvailabilityResponse(weekly=doctor.weekly_availability or {}, dates=doctor.date_availability)


@router.post("/me/photo", response_model=PhotoResponse)
def upload_photo(
    photo: UploadFile = File(...),
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> PhotoResponse:
    suffix = ALLOWED_IMAGE_TYPES.get(photo.content_type or "")
    if suffix is None:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Use JPEG, PNG, or WebP")

    destination = Path(settings.upload_dir) / f"doctor-{doctor.id}-{uuid4().hex}{suffix}"
    with destination.open("wb") as output:
        shutil.copyfileobj(photo.file, output)
    doctor.photo_url = f"/uploads/{destination.name}"
    db.commit()
    return PhotoResponse(photo_url=doctor.photo_url)
