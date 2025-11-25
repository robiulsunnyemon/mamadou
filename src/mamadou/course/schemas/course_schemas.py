from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new Course
class CourseCreate(BaseModel):
    name: str
    description: str
    image_url: str

# Schema for updating Course
class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

# Schema for Course response
class CourseResponse(BaseModel):
    id: str
    name: str
    description: str
    image_url: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
