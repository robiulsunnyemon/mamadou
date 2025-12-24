from fastapi import APIRouter, HTTPException,status,Depends
from typing import List

from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.lesson.models.lesson_model import LessonModel
from api_naturalize.notification.models.notification_model import notificationModel
from api_naturalize.notification.schemas.notification_schemas import NotificationCreate, NotificationUpdate, NotificationResponse
from api_naturalize.utils.user_info import get_user_info

router = APIRouter(prefix="/notifications", tags=["notifications"])

# # GET all notifications
# @router.get("/", response_model=List[NotificationResponse],status_code=status.HTTP_200_OK)
# async def get_all_notifications(skip: int = 0, limit: int = 10):
#
#     """
#     Get all notifications with pagination
#     """
#     notifications = await notificationModel.find_all().skip(skip).limit(limit).to_list()
#     return notifications
#
#


@router.get("/all/me", response_model=List[NotificationResponse])
async def get_notification_all_for_me(user_data: dict = Depends(get_user_info)):

    u_id = user_data.get("user_id")
    db_user = await UserModel.get(u_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found in DB")

    notifications = await notificationModel.find(
        notificationModel.user_id == db_user.id
    ).to_list()

    return notifications







#
# # GET notification by ID
# @router.get("/{notification_id}", response_model=NotificationResponse,status_code=status.HTTP_200_OK)
# async def get_notification(notification_id: str):
#
#     """
#     Get notification by ID
#     """
#     notification = await notificationModel.get(notification_id)
#     if not notification:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="notification not found")
#     return notification



# # POST create new notification
# @router.post("/", response_model=NotificationResponse,status_code=status.HTTP_201_CREATED)
async def create_notification(notification_data: NotificationCreate):

    """
    Create a new notification
    """
    notification_dict = notification_data.model_dump()
    notification = notificationModel(**notification_dict)
    await notification.create()
    return notification


@router.post("/lesson/complete/notification", response_model=NotificationResponse,status_code=status.HTTP_201_CREATED)
async def create_lesson_notification(lesson_id:str,user:dict=Depends(get_user_info)):
    db_user=await UserModel.get(user["user_id"])
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User does not exist")

    db_lesson=await LessonModel.get(lesson_id)
    if not db_lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson does not exist")


    new_notification=notificationModel(
        user_id=db_user.id,
        title="Great job!",
        description=f"You’ve successfully completed the lesson {db_lesson.name}.Keep going and start the next lesson now"
    )
    await new_notification.insert()
    return new_notification







# DELETE notification
@router.delete("/{notification_id}",status_code=status.HTTP_200_OK)
async def delete_notification(notification_id: str):
    
    """
    Delete notification by ID
    """
    notification = await notificationModel.get(notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="notification not found")

    await notification.delete()
    return {"message": "notification deleted successfully"}
