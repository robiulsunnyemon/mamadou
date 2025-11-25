from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new Lesson
class LessonCreate(BaseModel):
    name: str
    description: str
    image_url: str
    course_id: str

# Schema for updating Lesson
class LessonUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    course_id: Optional[str] = None

# Schema for Lesson response
class LessonResponse(BaseModel):
    id: str
    name: str
    description: str
    image_url: str
    course_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
