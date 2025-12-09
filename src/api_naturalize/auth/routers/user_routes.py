from fastapi import APIRouter, HTTPException, Depends,status
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.auth.schemas.user_schemas import UserCreate, UserUpdate, UserResponse, VerifyOTP, ResetPasswordRequest, \
    ResendOTPRequest
from api_naturalize.dashboard.routers.dashboard import get_in_progress_lessons
from api_naturalize.dashboard.schemas.dashboard import ExtendedDashboardResponse
from api_naturalize.leader_board.models.leader_board_model import LeaderBoardModel
from api_naturalize.lesson.models.lesson_model import LessonModel
from api_naturalize.question.models.question_model import QuestionModel

from api_naturalize.utils.email_config import SendOtpModel
from api_naturalize.utils.get_hashed_password import get_hashed_password,verify_password
from api_naturalize.utils.otp_generate import generate_otp
from api_naturalize.utils.token_generation import create_access_token

import requests

from api_naturalize.utils.user_info import get_user_info

router = APIRouter(prefix="/auth", tags=["Auth"])
user_router = APIRouter(prefix="/users", tags=["Users"])

# GET all users
@user_router.get("/", response_model=List[UserResponse],status_code=status.HTTP_200_OK)
async def get_all_users(skip: int = 0, limit: int = 20):
    """
    Get all users with pagination
    """
    users = await UserModel.find_all().skip(skip).limit(limit).to_list()
    return users


# GET user by ID
@user_router.get("/{id}", response_model=UserResponse,status_code=status.HTTP_200_OK)
async def get_user(id: str):
    """
    Get user by ID
    """
    user = await UserModel.get(id)
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
@user_router.patch("/{id}", response_model=UserResponse,status_code=status.HTTP_200_OK)
async def update_user(id: str, user_data: UserUpdate):
    """
    Update user information
    """
    user = await UserModel.get(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    await user.update({"$set": update_data})
    return await UserModel.get(id)


# DELETE user
@user_router.delete("/{id}",status_code=status.HTTP_200_OK)
async def delete_user(id: str):
    """
    Delete user by ID
    """
    user = await UserModel.get(id)
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



@router.post("/google-login",status_code=status.HTTP_201_CREATED)
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
    if db_user is None :
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
        token = create_access_token(data={"sub": email,"user_id": new_user.id})
        return {"access_token": token, "token_type": "bearer"}


    # 3️⃣ Generate JWT token
    token = create_access_token(data={"sub": db_user.email, "role": db_user.role.value, "user_id": db_user.id})
    return {"access_token": token, "token_type": "bearer"}







@user_router.get("/me", response_model=ExtendedDashboardResponse)
async def get_extended_dashboard_stats(user=Depends(get_user_info)):
    """
    Get extended dashboard statistics for a specific user including:
    - total_score from leaderboard
    - total_lessons
    - success_rate
    - user details
    - in-progress lessons (progress > 0 and < 100)
    """

    # Get user details
    id=user["user_id"]
    user = await UserModel.get(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert user model to UserResponse
    user_response = UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        is_verified=user.is_verified,
        profile_image=user.profile_image,
        auth_provider=user.auth_provider,
        created_at=user.created_at,
        updated_at=user.updated_at,
        role=user.role,
        otp=user.otp,
        account_status=user.account_status
    )

    # Get total_score from LeaderBoardModel
    leaderboard_data = await LeaderBoardModel.find_one(LeaderBoardModel.user_id == id)
    total_score = leaderboard_data.total_score if leaderboard_data else 0

    # Get total lessons count
    total_lessons = await LessonModel.find_all().count()

    # Calculate success rate
    total_questions = await QuestionModel.find_all().count()
    success_rate = (total_questions * total_score) / 100 if total_questions > 0 else 0.0

    # Get in-progress lessons (progress > 0 and < 100)
    in_progress_lessons = await get_in_progress_lessons(id)

    return ExtendedDashboardResponse(
        total_score=total_score,
        total_lessons=total_lessons,
        success_rate=success_rate,
        user_details=user_response,
        in_progress_lessons=in_progress_lessons
    )