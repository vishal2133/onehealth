import smtplib
from email.message import EmailMessage

from app.config import settings


def send_otp_email(email: str, code: str) -> None:
    if not settings.smtp_username or not settings.smtp_password:
        print(f"[OneHealth dev OTP] {email}: {code}")
        return

    message = EmailMessage()
    message["Subject"] = "Your OneHealth doctor login code"
    message["From"] = settings.smtp_from_email or settings.smtp_username
    message["To"] = email
    message.set_content(f"Your OneHealth verification code is {code}. It expires shortly.")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
