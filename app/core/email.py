from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://7361-109-107-242-140.ngrok-free.app")


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 465)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "False") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "True") == "True",
    USE_CREDENTIALS=True
)

fm = FastMail(conf)

async def send_verification_email(email: EmailStr, token: str):
    verification_link = f"{BASE_URL}/auth/verify-page?token={token}"
    message = MessageSchema(
        subject="Verify Your Email",
        recipients=[email],
        body=f"""
        <h3>Click the link to verify your email:</h3>
        <a href="{verification_link}">verification_link</a>
        <br><br>
        <small>If you didn’t create an account, you can ignore this email.</small>
        """,
        subtype=MessageType.html
    )
    try:
        await fm.send_message(message)
        print(f"Verification email sent to {email}")
    except Exception as e:
        print(f"Failed to send verification email: {e}")


async def send_password_reset_email(email: EmailStr, token: str):
    reset_link = f"{BASE_URL}/auth/reset-password-page?token={token}"
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email], 
        body=f"""
        <h3>Click the link below to reset your password:</h3>
        <a href='{reset_link}'>reset_link</a>
        <br><br>
        <small>If you didn’t request this, you can safely ignore this email.</small>
        """,
        subtype=MessageType.html
    )
    try:
        await fm.send_message(message)
        print(f"Password reset email sent to {email}")
    except Exception as e:
        print(f"Failed to send password reset email: {e}")

