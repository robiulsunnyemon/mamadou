from fastapi import APIRouter, HTTPException,status
from typing import List
from api_naturalize.subscription_plan.models.subscription_plan_model import SubscriptionPlanModel
from api_naturalize.subscription_plan.schemas.subscription_plan_schemas import SubscriptionplanCreate, SubscriptionplanUpdate, SubscriptionplanResponse

router = APIRouter(prefix="/subscription_plans", tags=["subscription_plans"])

# GET all subscription_plans
@router.get("/", response_model=List[SubscriptionplanResponse],status_code=status.HTTP_200_OK)
async def get_all_subscription_plans(skip: int = 0, limit: int = 10):
    
    """
    Get all subscription_plans with pagination
    """
    subscription_plans = await SubscriptionPlanModel.find_all().skip(skip).limit(limit).to_list()
    return subscription_plans

# GET subscription_plan by ID
@router.get("/{subscription_plan_id}", response_model=SubscriptionplanResponse,status_code=status.HTTP_200_OK)
async def get_subscription_plan(subscription_plan_id: str):
    
    """
    Get subscription_plan by ID
    """
    subscription_plan = await SubscriptionPlanModel.get(subscription_plan_id)
    if not subscription_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SubscriptionPlan not found")
    return subscription_plan

# POST create new subscription_plan
@router.post("/", response_model=SubscriptionplanResponse,status_code=status.HTTP_201_CREATED)
async def create_subscription_plan(subscription_plan_data: SubscriptionplanCreate):
    
    """
    Create a new subscription_plan
    """
    subscription_plan_dict = subscription_plan_data.model_dump()
    subscription_plan = SubscriptionPlanModel(**subscription_plan_dict)
    await subscription_plan.create()
    return subscription_plan

# PATCH update subscription_plan
@router.patch("/{subscription_plan_id}", response_model=SubscriptionplanResponse,status_code=status.HTTP_200_OK)
async def update_subscription_plan(subscription_plan_id: str, subscription_plan_data: SubscriptionplanUpdate):
    
    """
    Update subscription_plan information
    """
    subscription_plan = await SubscriptionPlanModel.get(subscription_plan_id)
    if not subscription_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SubscriptionPlan not found")

    update_data = subscription_plan_data.model_dump(exclude_unset=True)
    await subscription_plan.update({"$set": update_data})
    return await SubscriptionPlanModel.get(subscription_plan_id)

# DELETE subscription_plan
@router.delete("/{subscription_plan_id}",status_code=status.HTTP_200_OK)
async def delete_subscription_plan(subscription_plan_id: str):
    
    """
    Delete subscription_plan by ID
    """
    subscription_plan = await SubscriptionPlanModel.get(subscription_plan_id)
    if not subscription_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SubscriptionPlan not found")

    await subscription_plan.delete()
    return {"message": "SubscriptionPlan deleted successfully"}
