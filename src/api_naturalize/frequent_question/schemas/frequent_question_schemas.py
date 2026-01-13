from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new FrequentQuestion
class FrequentquestionCreate(BaseModel):
    question: str
    answer: str

# Schema for updating FrequentQuestion
class FrequentquestionUpdate(BaseModel):
    user_id: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None

# Schema for FrequentQuestion response
class FrequentquestionResponse(BaseModel):
    id: str
    user_id: str
    question: str
    answer: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
