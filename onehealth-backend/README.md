# OneHealth Doctor Backend

FastAPI and PostgreSQL backend for the OneHealth doctor portal.

## Features

- Pre-registered doctor login through email OTP and JWT
- Doctor profile, profile photo, weekly schedule, and date-specific availability
- Doctor-scoped appointments and patients
- Doctor-scoped conversation history, REST messages, and authenticated WebSockets
- PostgreSQL migrations through Alembic
- Development seed data matching Tanaya, Andro, and Ritefood

## Local setup

Use Python 3.11 as requested for this project.

```powershell
cd onehealth-backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Create a PostgreSQL database named `onehealth`, then update `DATABASE_URL` in `.env`.

```powershell
alembic upgrade head
python seed.py
python -m uvicorn app.main:app --reload --port 8001
```

Open `http://localhost:8001/docs` for the interactive API documentation.

The seeded login is `sarah.carter@onehealth.com`. In development, `/auth/send-otp`
returns and logs the configured `DEV_OTP_CODE`, which defaults to `123456`.

## Frontend integration

Set a frontend API base URL such as `VITE_API_URL=http://localhost:8001`.

1. Call `POST /auth/send-otp` with `{ "email": "..." }`.
2. Call `POST /auth/verify-otp` with `{ "email": "...", "code": "123456" }`.
3. Store `accessToken` and send `Authorization: Bearer <token>` on protected requests.
4. Connect chat with `ws://localhost:8001/chat/ws/{conversationId}?token=<token>`.

API responses use camelCase keys so they can replace the current frontend mock objects
with minimal mapping.
