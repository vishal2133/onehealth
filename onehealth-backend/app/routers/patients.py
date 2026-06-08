from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_doctor
from app.database import get_db
from app.models import Appointment, Conversation, Doctor, Patient
from app.schemas.patient import PatientResponse


router = APIRouter(prefix="/patients", tags=["patients"])


def patient_ids_for_doctor(db: Session, doctor_id: int):
    appointment_ids = select(Appointment.patient_id).where(Appointment.doctor_id == doctor_id)
    conversation_ids = select(Conversation.patient_id).where(Conversation.doctor_id == doctor_id)
    return appointment_ids.union(conversation_ids)


@router.get("/", response_model=list[PatientResponse])
def list_patients(
    service: str | None = None,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> list[Patient]:
    query = select(Patient).where(Patient.id.in_(patient_ids_for_doctor(db, doctor.id))).order_by(Patient.name)
    if service:
        query = query.where(Patient.service == service)
    return list(db.scalars(query).all())


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
) -> Patient:
    patient = db.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.id.in_(patient_ids_for_doctor(db, doctor.id)),
        )
    )
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient
