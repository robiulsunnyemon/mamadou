
from pydantic import BaseModel, EmailStr
from email.message import EmailMessage
import aiosmtplib
import os

APP_PASSWORD = os.getenv("APP_PASSWORD")
EMAIL = os.getenv("EMAIL")
HOST_NAME = os.getenv("HOST_NAME")



# 🔹 Pydantic v2 model
class SendOtpModel(BaseModel):
    email: EmailStr
    otp: str

    model_config = {"from_attributes": True}


async def send_otp(otp_user: SendOtpModel):
    """
    Send OTP to user's email asynchronously
    """
    message = EmailMessage()
    message["From"] = EMAIL
    message["To"] = otp_user.email
    message["Subject"] = "🔑 Your OTP Code"
    message.set_content(f"Your OTP code is: {otp_user.otp}")

    await aiosmtplib.send(
        message,
        hostname=HOST_NAME,
        port=465,
        use_tls=True,
        username=EMAIL,
        password=APP_PASSWORD,
    )