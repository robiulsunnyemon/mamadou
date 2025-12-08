from pydantic import BaseModel, EmailStr,Field
from typing import Optional
from datetime import datetime

from api_naturalize.utils.account_status import AccountStatus
from api_naturalize.utils.user_role import UserRole


class UserCreate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    phone_number: Optional[str]
    password: Optional[str] = None
    auth_provider: str = "email"


class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    profile_image: Optional[str]


class UserResponse(BaseModel):
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    phone_number: Optional[str]
    is_verified: bool
    profile_image: Optional[str]
    auth_provider: str
    created_at: datetime
    updated_at: datetime
    role: Optional[UserRole] = Field(default=UserRole.USER)
    otp:Optional[str]
    account_status: AccountStatus

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str



class ResendOTPRequest(BaseModel):
    email: EmailStr



class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str