from pydantic import BaseModel
from typing import Optional,List
from datetime import datetime

# Schema for creating new SubscriptionPlan
class SubscriptionplanCreate(BaseModel):
    title: str
    plan_price: float
    duration: str
    features: List[str]

# Schema for updating SubscriptionPlan
class SubscriptionplanUpdate(BaseModel):
    title: Optional[str] = None
    plan_price: Optional[float] = None
    duration: Optional[str] = None
    features: Optional[List[str]] = None

# Schema for SubscriptionPlan response
class SubscriptionplanResponse(BaseModel):
    id: str
    title: str
    plan_price: float
    duration: str
    features: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True