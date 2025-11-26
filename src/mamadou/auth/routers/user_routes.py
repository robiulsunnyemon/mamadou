from fastapi import APIRouter, HTTPException, Depends,status
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from mamadou.auth.models.user_model import UserModel
from mamadou.auth.schemas.user_schemas import UserCreate, UserUpdate, UserResponse, VerifyOTP, ResetPasswordRequest, \
    ResendOTPRequest
from mamadou.utils.email_config import SendOtpModel
from mamadou.utils.get_hashed_password import get_hashed_password,verify_password
from mamadou.utils.otp_generate import generate_otp
from mamadou.utils.token_generation import create_access_token

router = APIRouter(prefix="/users", tags=["Auth & User"])


# GET all users
@router.get("/", response_model=List[UserResponse],status_code=status.HTTP_200_OK)
async def get_all_users(skip: int = 0, limit: int = 10):
    """
    Get all users with pagination
    """
    users = await UserModel.find_all().skip(skip).limit(limit).to_list()
    return users


# GET user by ID
@router.get("/{user_id}", response_model=UserResponse,status_code=status.HTTP_200_OK)
async def get_user(user_id: str):
    """
    Get user by ID
    """
    user = await UserModel.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# POST create new user
@router.post("/" ,response_model=UserResponse,status_code=status.HTTP_201_CREATED)
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
    ##await send_otp(send_otp_data)
    return new_user


# PATCH update user
@router.patch("/{user_id}", response_model=UserResponse,status_code=status.HTTP_200_OK)
async def update_user(user_id: str, user_data: UserUpdate):
    """
    Update user information
    """
    user = await UserModel.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    await user.update({"$set": update_data})
    return await UserModel.get(user_id)


# DELETE user
@router.delete("/{user_id}",status_code=status.HTTP_200_OK)
async def delete_user(user_id: str):
    """
    Delete user by ID
    """
    user = await UserModel.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user.delete()
    return {"message": "User deleted successfully"}




@router.post("/otp_verify", status_code=status.HTTP_200_OK)
async def verify_otp(user:VerifyOTP):
    db_user =await UserModel.find_one(UserModel.email == user.email)
    if db_user is None :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    if user.otp != db_user.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Wrong OTP")

    db_user.is_verified=True
    await db_user.save()
    return {"message":"You have  verified","data":db_user}




@router.post("/login", status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db_user = await UserModel.find_one(
        {"$or": [{"email": form_data.username}, {"phone_number": form_data.username}]}
    )

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(form_data.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong password")

    if not db_user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your account is not verified with OTP")

    token = create_access_token(data={"sub": db_user.email, "role": db_user.role.value, "user_id": db_user.id})
    return {"access_token": token, "token_type": "bearer"}




@router.post("/resend_otp", status_code=status.HTTP_200_OK)
async def resend_otp(request: ResendOTPRequest):
    db_user = await UserModel.find_one(UserModel.email == request.email)
    if db_user is None :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    otp=generate_otp()
    db_user.otp=otp
    await db_user.save()
    send_otp_data = SendOtpModel(email=db_user.email, otp=db_user.otp)
    ##await send_otp(send_otp_data)
    return {
        "message": "User registered successfully.Please check your email.A 6 digit otp has been sent.",
        "data":db_user,
        "otp":db_user.otp
    }





@router.post("/reset_password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest):
    db_user = await UserModel.find_one(UserModel.email == request.email)
    if db_user is None :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")

    if not db_user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Your account is not verified with otp")

    hashed_password = get_hashed_password(request.new_password)
    db_user.password = hashed_password
    await db_user.save()
    return {"message":"successfully reset password"}




