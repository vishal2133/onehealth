from datetime import date, time

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Appointment, Conversation, Doctor, Message, Patient


WEEKLY = {
    "Monday": {"active": True, "start": "09:00", "end": "17:00"},
    "Tuesday": {"active": True, "start": "09:00", "end": "17:00"},
    "Wednesday": {"active": True, "start": "09:00", "end": "13:00"},
    "Thursday": {"active": True, "start": "09:00", "end": "17:00"},
    "Friday": {"active": True, "start": "09:00", "end": "17:00"},
    "Saturday": {"active": False, "start": "09:00", "end": "12:00"},
    "Sunday": {"active": False, "start": "09:00", "end": "12:00"},
}

PATIENTS = [
    ("Nisha Sharma", 29, "Female", "Tanaya", "PCOS follow-up and cycle review"),
    ("Rohan Mehta", 34, "Male", "Andro", "Stress fatigue and gym nutrition review"),
    ("Aditi Rao", 41, "Female", "Ritefood", "Gestational diabetes meal plan"),
    ("Kabir Kapoor", 52, "Male", "Andro", "Annual wellness check and panel review"),
    ("Pooja Iyer", 31, "Female", "Tanaya", "First trimester pregnancy wellness"),
    ("Vikram Singh", 45, "Male", "Ritefood", "Hypertension sodium-reduction consult"),
]


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(Doctor).where(Doctor.email == "sarah.carter@onehealth.com")):
            print("Seed data already exists.")
            return

        doctor = Doctor(
            name="Dr. Sarah Carter",
            email="sarah.carter@onehealth.com",
            specialty="Lead Gynecologist",
            department="Tanaya Unit",
            phone="+91 98765 43210",
            qualifications="MBBS, MD (Obstetrics & Gynecology)",
            reg_number="MCI-2024-GYN-08472",
            experience="12 Years",
            hospital="OneHealth Medical Center, Bengaluru",
            weekly_availability=WEEKLY,
            date_availability={
                "2026-06-04": {"isAvailable": True, "startTime": "09:00", "endTime": "17:30"},
                "2026-06-05": {"isAvailable": True, "startTime": "09:00", "endTime": "14:00"},
            },
        )
        db.add(doctor)
        db.flush()

        appointment_dates = [
            (date(2026, 6, 4), time(9, 30), "scheduled"),
            (date(2026, 6, 4), time(11, 0), "scheduled"),
            (date(2026, 6, 4), time(14, 30), "scheduled"),
            (date(2026, 6, 4), time(16, 0), "scheduled"),
            (date(2026, 6, 5), time(10, 0), "scheduled"),
            (date(2026, 5, 18), time(12, 30), "completed"),
        ]

        for index, (name, age, gender, service, reason) in enumerate(PATIENTS):
            patient = Patient(
                name=name,
                email=f"{name.lower().replace(' ', '.')}@example.com",
                phone=f"+91 90000 {index + 10000}",
                age=age,
                gender=gender,
                service=service,
            )
            db.add(patient)
            db.flush()
            appt_date, appt_time, status = appointment_dates[index]
            db.add(
                Appointment(
                    doctor_id=doctor.id,
                    patient_id=patient.id,
                    date=appt_date,
                    time=appt_time,
                    reason=reason,
                    status=status,
                    category=service,
                )
            )
            conversation = Conversation(doctor_id=doctor.id, patient_id=patient.id)
            db.add(conversation)
            db.flush()
            db.add_all(
                [
                    Message(
                        conversation_id=conversation.id,
                        sender_type="patient",
                        sender_id=patient.id,
                        content=f"Hello doctor, I wanted to discuss my {reason.lower()}.",
                        is_read=index > 1,
                    ),
                    Message(
                        conversation_id=conversation.id,
                        sender_type="doctor",
                        sender_id=doctor.id,
                        content="Thank you for the update. I will review this before our consultation.",
                        is_read=True,
                    ),
                ]
            )

        db.commit()
        print("Seeded doctor, patients, appointments, conversations, and messages.")


if __name__ == "__main__":
    seed()
