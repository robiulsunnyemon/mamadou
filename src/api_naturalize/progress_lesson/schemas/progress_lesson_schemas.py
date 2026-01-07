from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new ProgressLesson
class ProgresslessonCreate(BaseModel):
    lesson_id: str
    course_id: str ##add
    progress: float
    user_id: str

# Schema for updating ProgressLesson
class ProgresslessonUpdate(BaseModel):
    lesson_id: Optional[str] = None
    progress: Optional[float] = None
    user_id: Optional[str] = None

# Schema for ProgressLesson response
class ProgresslessonResponse(BaseModel):
    id: str
    lesson_id: str
    progress: float
    user_id: str
    course_id: str ##add
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for filtered lesson response
class FilteredLessonResponse(BaseModel):
    id: str
    name: str
    description: str
    image_url: str
    course_id: str
    my_progress: float
    total_right_answers: int
    total_questions: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DashboardStatsResponse(BaseModel):
    total_questions: int
    total_lessons: int
    success_rate: float