from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new notification
class NotificationCreate(BaseModel):
    user_id:str
    title: str
    description: str

# Schema for updating notification
class NotificationUpdate(BaseModel):
    user_id:Optional[str]=None
    title: Optional[str] = None
    description: Optional[str] = None

# Schema for notification response
class NotificationResponse(BaseModel):
    id: str
    user_id:str
    title: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
