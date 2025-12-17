from fastapi import APIRouter, HTTPException, Depends,status,File, UploadFile, Form,Request
from typing import List
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.auth.schemas.user_schemas import UserUpdate, UserResponse
from api_naturalize.dashboard.routers.dashboard import get_in_progress_lessons
from api_naturalize.dashboard.schemas.dashboard import ExtendedDashboardResponse, ExtendedAppUserResponse
from api_naturalize.leader_board.models.leader_board_model import LeaderBoardModel
from api_naturalize.lesson.models.lesson_model import LessonModel
from api_naturalize.question.models.question_model import QuestionModel
from api_naturalize.utils.user_info import get_user_info
import aiofiles
import os
import uuid

user_router = APIRouter(prefix="/users", tags=["Users"])


# GET all users
@user_router.get("/", response_model=List[UserResponse],status_code=status.HTTP_200_OK)
async def get_all_users(skip: int = 0, limit: int = 20):
    """
    Get all users with pagination
    """
    users = await UserModel.find_all().sort("-created_at").skip(skip).limit(limit).to_list()
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

#
# @user_router.patch("/update/info", status_code=status.HTTP_200_OK)
# async def update_user(user_data: UserUpdate, user_info: dict = Depends(get_user_info)):
#
#     user_id = user_info["user_id"]
#
#
#     user_obj = await UserModel.get(user_id)
#     if not user_obj:
#         raise HTTPException(status_code=404, detail="User not found")
#
#
#     update_data = user_data.model_dump(exclude_unset=True)
#
#     if not update_data:
#         raise HTTPException(status_code=400, detail="No data provided for update")
#
#
#     await user_obj.set(update_data)
#
#
#     return {"message":"Successfully update profile"}
#


@user_router.patch("/update/info", status_code=status.HTTP_200_OK)
async def update_user(
        request: Request,
        first_name: str = Form(None),
        last_name: str = Form(None),
        email: str = Form(None),
        phone_number: str = Form(None),
        profile_image: UploadFile = File(None),
        user_info: dict = Depends(get_user_info)
):
    user_id = user_info["user_id"]
    user_obj = await UserModel.get(user_id)

    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {}

    fields = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone_number": phone_number
    }

    for key, value in fields.items():
        if value is not None and str(value).strip() != "":
            update_data[key] = value


    if profile_image:
        upload_dir = "static/profile_images"
        os.makedirs(upload_dir, exist_ok=True)

        extension = os.path.splitext(profile_image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        base_url = str(request.base_url).rstrip('/')
        if "localhost" not in base_url:
            base_url = base_url.replace("http://", "https://")

        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await profile_image.read()
                await out_file.write(content)

            update_data["profile_image"] = f"{base_url}/{file_path}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save image: {str(e)}")

    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")

    await user_obj.set(update_data)

    return {"message": "Successfully updated profile", "data": update_data}



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




@user_router.get("/info/me", response_model=ExtendedAppUserResponse,status_code=status.HTTP_200_OK)
async def get_extended_dashboard_stats(user: dict = Depends(get_user_info)):
    user_id = user["user_id"]
    db_user = await UserModel.get(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")


    # Convert user model to UserResponse
    user_response = UserResponse(
        id=db_user.id,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        email=db_user.email,
        phone_number=db_user.phone_number,
        is_verified=db_user.is_verified,
        profile_image=db_user.profile_image,
        auth_provider=db_user.auth_provider,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at,
        role=db_user.role,
        otp=db_user.otp,
        account_status=db_user.account_status
    )

    # Get total_score from LeaderBoardModel
    leaderboard_data = await LeaderBoardModel.find_one(LeaderBoardModel.user_id == user_id)
    total_score = leaderboard_data.total_score if leaderboard_data else 0

    # Get total lessons count
    total_lessons = await LessonModel.find_all().count()

    # Calculate success rate
    total_questions = await QuestionModel.find_all().count()
    success_rate = (total_questions * total_score) / 100 if total_questions > 0 else 0.0

    # Get in-progress lessons (progress > 0 and < 100)
    in_progress_lessons = await get_in_progress_lessons(user_id)

    return ExtendedAppUserResponse(
        total_score=total_score,
        total_lessons=total_lessons,
        success_rate=success_rate,
        user_details=user_response,
        in_progress_lessons=in_progress_lessons
    )