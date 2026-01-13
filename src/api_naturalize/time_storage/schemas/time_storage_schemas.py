from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new TimeStorage
class TimestorageCreate(BaseModel):
    total_time: int

# Schema for updating TimeStorage
class TimestorageUpdate(BaseModel):
    user_id: Optional[str] = None
    total_time: Optional[int] = None

# Schema for TimeStorage response
class TimestorageResponse(BaseModel):
    id: str
    user_id: str
    total_time: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
