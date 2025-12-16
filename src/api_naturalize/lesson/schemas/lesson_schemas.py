from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import List

from api_naturalize.progress_lesson.schemas.progress_lesson_schemas import ProgresslessonResponse
from api_naturalize.question.schemas.question_schemas import QuestionResponse


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

class LessonResponseAdmin(BaseModel):
    id: str
    name: str
    description: str
    image_url: str
    course_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for Lesson response

class LessonResponse(BaseModel):
    id: str
    name: str
    description: str
    image_url: str
    course_id: str
    questions: List[QuestionResponse] = []
    my_progress: float = 0.0  # Only progress percentage
    total_right_answers: int = 0
    total_questions: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Bulk Lesson Creation Schema
class BulkLessonCreate(BaseModel):
    lessons: List[LessonCreate]

class BulkLessonResponse(BaseModel):
    message: str
    created_count: int
    lessons: List[LessonResponse]