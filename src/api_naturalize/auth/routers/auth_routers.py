"""
Login endpoint now returns complete user data

Previously: Only returned access_token
Now: Returns access_token + user object with name, email, etc.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.auth.schemas.user_schemas import (
    UserCreate, UserUpdate, UserResponse, VerifyOTP, 
    ResetPasswordRequest, ResendOTPRequest
)
from api_naturalize.notification.routers.notification_routes import create_notification
from api_naturalize.notification.schemas.notification_schemas import NotificationCreate
from api_naturalize.utils.email_config import SendOtpModel, send_otp
from api_naturalize.utils.get_hashed_password import get_hashed_password, verify_password
from api_naturalize.utils.otp_generate import generate_otp
from api_naturalize.utils.token_generation import create_access_token
import requests
from api_naturalize.utils.user_role import UserRole

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    hashed_password = get_hashed_password(user.password)
    db_user = await UserModel.find_one(UserModel.email == user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    otp = generate_otp()
    new_user = UserModel(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        password=hashed_password,
        otp=otp
    )
    await new_user.insert()
    send_otp_data = SendOtpModel(email=new_user.email, otp=new_user.otp)
    await send_otp(send_otp_data)
    return new_user


@router.post("/signup/admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(user: UserCreate):
    hashed_password = get_hashed_password(user.password)
    db_user = await UserModel.find_one(UserModel.email == user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    otp = generate_otp()
    new_user = UserModel(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        password=hashed_password,
        otp=otp,
        role=UserRole.ADMIN
    )
    await new_user.insert()
    send_otp_data = SendOtpModel(email=new_user.email, otp=new_user.otp)
    await send_otp(send_otp_data)
    return new_user


@router.post("/otp_verify", status_code=status.HTTP_200_OK)
async def verify_otp(user: VerifyOTP):
    db_user = await UserModel.find_one(UserModel.email == user.email)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.otp != db_user.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong OTP")

    db_user.is_verified = True
    notification = NotificationCreate(
        user_id=db_user.id,
        title=f"Welcome {db_user.first_name} {db_user.last_name}",
        description="Your account has been created successfully. Let's get started with your first theme"
    )
    await create_notification(notification)
    await db_user.save()
    return {"message": "You have verified", "data": db_user}


# Login now returns user data!  *** _ ***
@router.post("/login", status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint returns complete user data
    
    Now returns:
    {
        "access_token": "...",
        "token_type": "bearer",
        "user": {
            "id": "...",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "...",
            "profile_image": "...",
            "role": "admin"
        }
    }
    """
    db_user = await UserModel.find_one(
        {"$or": [{"email": form_data.username}, {"phone_number": form_data.username}]}
    )

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(form_data.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong password")

    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your account is not verified with OTP"
        )

    notification = NotificationCreate(
        user_id=db_user.id,
        title=f"Welcome back! {db_user.first_name} {db_user.last_name}",
        description="You're successfully logged in. Let's continue where you left off"
    )
    await create_notification(notification)

    token = create_access_token(
        data={
            "sub": db_user.email,
            "role": db_user.role.value,
            "user_id": db_user.id
        }
    )

    # Build complete user response *** _ ***
    user_dict = db_user.model_dump()
    user_data = {
        "id": user_dict.get("id"),
        "email": user_dict.get("email"),
        "username": user_dict.get("email", "").split("@")[0],  # Create username from email
        # Include name fields!
        "name": f"{user_dict.get('first_name', '')} {user_dict.get('last_name', '')}".strip(),
        "fname": user_dict.get("first_name", ""),
        "lname": user_dict.get("last_name", ""),
        "first_name": user_dict.get("first_name"),
        "last_name": user_dict.get("last_name"),
        "phone_number": user_dict.get("phone_number"),
        "profile_image": user_dict.get("profile_image"),
        "avatar_url": user_dict.get("profile_image"),
        "role": user_dict.get("role", "user"),
    }

    # Return token + user data
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data  # *** _ *** Include user object
    }


@router.post("/resend_otp", status_code=status.HTTP_200_OK)
async def resend_otp(request: ResendOTPRequest):
    db_user = await UserModel.find_one(UserModel.email == request.email)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    otp = generate_otp()
    db_user.otp = otp
    await db_user.save()
    send_otp_data = SendOtpModel(email=db_user.email, otp=db_user.otp)
    await send_otp(send_otp_data)

    return {
        "message": "User registered successfully. Please check your email. A 6 digit OTP has been sent.",
        "data": db_user,
        "otp": db_user.otp
    }


@router.post("/reset_password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest):
    db_user = await UserModel.find_one(UserModel.email == request.email)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your account is not verified with OTP"
        )

    hashed_password = get_hashed_password(request.new_password)
    db_user.password = hashed_password

    notification = NotificationCreate(
        user_id=db_user.id,
        title="Password updated successfully",
        description="Your account password was changed successfully. If this wasn't you, please reset your password immediately."
    )
    await create_notification(notification)

    await db_user.save()
    return {"message": "successfully reset password"}


@router.post("/google-login", status_code=status.HTTP_201_CREATED)
async def google_login_token(access_token: str):
    if access_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="please give me token")

    response = requests.get(
        f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}'
    )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Google token")

    user_info = response.json()
    email = user_info["email"]
    name = user_info.get("name", "")
    picture = user_info.get("picture", "")

    db_user = await UserModel.find_one(UserModel.email == email)
    if db_user is None:
        new_user = UserModel(
            first_name=name.split(" ")[0] if name else "",
            last_name=" ".join(name.split(" ")[1:]) if len(name.split(" ")) > 1 else "",
            email=email,
            phone_number="",
            password=None,
            is_verified=True,
            profile_image=picture,
            auth_provider="google",
        )
        await new_user.insert()
        token = create_access_token(data={"sub": email, "user_id": new_user.id})
        return {"access_token": token, "token_type": "bearer"}

    notification = NotificationCreate(
        user_id=db_user.id,
        title="Account created securely",
        description="You signed up using your Google account. No password needed—your account is protected."
    )
    await create_notification(notification)

    token = create_access_token(
        data={"sub": db_user.email, "role": db_user.role.value, "user_id": db_user.id}
    )
    return {"access_token": token, "token_type": "bearer"}

# *** __ ***