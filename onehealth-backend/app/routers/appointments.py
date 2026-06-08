from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_doctor
from app.database import get_db
from app.models import Appointment, Doctor
from app.schemas.appointment import AppointmentResponse


router = APIRouter(prefix="/appointments", tags=["appointments"])


def serialize(appointment: Appointment) -> AppointmentResponse:
    return AppointmentResponse(
        id=appointment.id,
        date=appointment.date,
        time=appointment.time,
        patient_id=appointment.patient_id,
        patient_name=appointment.patient.name,
        age=appointment.patient.age,
        gender=appointment.patient.gender,
        category=appointment.category,
        reason=appointment.reason,
        status=appointment.status,
        is_today=appointment.date == date.today(),
    )


@router.get("/", response_model=list[AppointmentResponse])
def list_appointments(
    appointment_date: date | None = Query(None, alias="date"),
    category: str | None = None,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> list[AppointmentResponse]:
    query = (
        select(Appointment)
        .options(joinedload(Appointment.patient))
        .where(Appointment.doctor_id == doctor.id)
        .order_by(Appointment.date.desc(), Appointment.time)
    )
    if appointment_date:
        query = query.where(Appointment.date == appointment_date)
    if category:
        query = query.where(Appointment.category == category)
    return [serialize(item) for item in db.scalars(query).all()]


@router.get("/today", response_model=list[AppointmentResponse])
def todays_appointments(
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> list[AppointmentResponse]:
    query = (
        select(Appointment)
        .options(joinedload(Appointment.patient))
        .where(Appointment.doctor_id == doctor.id, Appointment.date == date.today())
        .order_by(Appointment.time)
    )
    return [serialize(item) for item in db.scalars(query).all()]
