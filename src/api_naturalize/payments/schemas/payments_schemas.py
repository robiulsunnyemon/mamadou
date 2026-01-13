from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schema for creating new Payments
class PaymentsCreate(BaseModel):
    amount: float
    subscription_name: str

# Schema for updating Payments
class PaymentsUpdate(BaseModel):
    user_id: Optional[str] = None
    amount: Optional[float] = None
    subscription_name: Optional[str] = None

# Schema for Payments response
class PaymentsResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    subscription_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
