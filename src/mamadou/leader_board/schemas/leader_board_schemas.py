from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new LeaderBoard
class LeaderboardCreate(BaseModel):
    user_id: str
    total_score: int

# Schema for updating LeaderBoard
class LeaderboardUpdate(BaseModel):
    user_id: Optional[str] = None
    total_score: Optional[int] = None

# Schema for LeaderBoard response
class LeaderboardResponse(BaseModel):
    id: str
    user_id: str
    total_score: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
