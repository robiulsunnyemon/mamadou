from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import List
# Schema for creating new Question
class QuestionCreate(BaseModel):
    name: str
    lesson_id: str
    difficulty: str
    course_id: str
    options: List[str]
    correct_answer: str

# Schema for updating Question
class QuestionUpdate(BaseModel):
    name: Optional[str] = None
    lesson_id: Optional[str] = None
    difficulty: Optional[str] = None
    course_id: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None

# Schema for Question response
class QuestionResponse(BaseModel):
    id: str
    name: str
    lesson_id: str
    difficulty: str
    course_id: str
    options: List[str]
    correct_answer: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
