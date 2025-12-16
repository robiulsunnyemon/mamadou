from pydantic import BaseModel
from typing import Optional,List
from datetime import datetime

from api_naturalize.lesson.schemas.lesson_schemas import LessonResponse


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
class CourseResponseAdmin(BaseModel):
    id: str
    name: str
    description: str
    image_url: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



# Schema for Course response
class CourseResponse(BaseModel):
    id: str
    name: str
    description: str
    image_url: str
    lessons: List[LessonResponse] = []  # Nested lessons
    total_questions: int = 0  # New field for total questions in this course
    created_at: datetime
    updated_at: datetime
    course_progress:Optional[float]

    class Config:
        from_attributes = True
