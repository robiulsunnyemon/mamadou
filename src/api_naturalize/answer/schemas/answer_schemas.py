from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new Answer
class AnswerCreate(BaseModel):
    question_id: str
    submit_answer: str



# Schema for updating Answer
class AnswerUpdate(BaseModel):
    course_id: Optional[str] = None
    lesson_id: Optional[str] = None
    question_id: Optional[str] = None
    submit_answer: Optional[str] = None
    right_answer: Optional[str] = None


# Schema for Answer response
class AnswerResponse(BaseModel):
    id: str
    user_id: str
    course_id: str
    lesson_id: str
    question_id: str
    submit_answer: str
    right_answer: str
    score: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
