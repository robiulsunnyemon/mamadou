from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.database.database import get_database
from api_naturalize.payments.models.payments_model import PaymentsModel
from api_naturalize.payments.schemas.payments_schemas import PaymentsCreate, PaymentsUpdate, PaymentsResponse
from api_naturalize.utils.user_info import get_user_info
from datetime import datetime, timedelta, timezone
from typing import Dict




router = APIRouter(prefix="/paymentss", tags=["paymentss"])

# GET all paymentss
@router.get("/", response_model=List[PaymentsResponse],status_code=status.HTTP_200_OK)
async def get_all_paymentss(skip: int = 0, limit: int = 10):
    
    """
    Get all paymentss with pagination
    """
    paymentss = await PaymentsModel.find_all().skip(skip).limit(limit).to_list()
    return paymentss

# GET payments by ID
@router.get("/{payments_id}", response_model=PaymentsResponse,status_code=status.HTTP_200_OK)
async def get_payments(payments_id: str):
    
    """
    Get payments by ID
    """
    payments = await PaymentsModel.get(payments_id)
    if not payments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payments not found")
    return payments

# POST create new payments
@router.post("/", response_model=PaymentsResponse,status_code=status.HTTP_201_CREATED)
async def create_payments(payments_data: PaymentsCreate,user_data:dict=Depends(get_user_info)):
    
    """
    Create a new payments
    """
    db_user=await UserModel.get(user_data["user_id"])
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User does not exist")
    payments_dict = payments_data.model_dump()
    payments_dict["user_id"]=db_user.id
    payments = PaymentsModel(**payments_dict)
    await db_user.update(
        {"$set": {"plan": payments_data.subscription_name}}
    )
    await payments.create()
    return payments

# PATCH update payments
@router.patch("/{payments_id}", response_model=PaymentsResponse,status_code=status.HTTP_200_OK)
async def update_payments(payments_id: str, payments_data: PaymentsUpdate):
    
    """
    Update payments information
    """
    payments = await PaymentsModel.get(payments_id)
    if not payments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payments not found")

    update_data = payments_data.model_dump(exclude_unset=True)
    await payments.update({"$set": update_data})
    return await PaymentsModel.get(payments_id)

# DELETE payments
@router.delete("/{payments_id}",status_code=status.HTTP_200_OK)
async def delete_payments(payments_id: str):
    
    """
    Delete payments by ID
    """
    payments = await PaymentsModel.get(payments_id)
    if not payments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payments not found")

    await payments.delete()
    return {"message": "Payments deleted successfully"}





@router.get("/payments/total-last-30days")
async def get_total_amount_last_6_months():
    try:

        six_months_ago = datetime.now(timezone.utc) - timedelta(days=30)


        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": six_months_ago}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"}
                }
            }
        ]


        db = get_database()
        collection = db["paymentss"]

        results = []
        cursor = collection.aggregate(pipeline)
        total_sum = 0.0


        async for doc in cursor:
            results.append(doc)


        if results:
            total_sum = results[0].get("total", 0.0)

        return {
            "status": "success",
            "total_amount": round(total_sum, 2),
            "time_period": "last 30days"
        }

    except Exception as e:
        print(f"Stats Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/free-plan", status_code=status.HTTP_200_OK)
async def get_free_plan_member():
    free_plan_members = await PaymentsModel.find(
        PaymentsModel.subscription_name == "Free Plan"
    ).count()

    total_user = await UserModel.find_all().count()

    return {
        "free_plan_member": free_plan_members,
        "total_user": total_user
    }




@router.get("/user/basic-plan", status_code=status.HTTP_200_OK)
async def get_basic_plan_member():
    basic_plan_members = await PaymentsModel.find(
        PaymentsModel.subscription_name == "Basic Plan"
    ).count()

    total_user = await UserModel.find_all().count()

    return {
        "basic_plan_member": basic_plan_members,
        "total_user": total_user
    }



@router.get("/user/premium-plan", status_code=status.HTTP_200_OK)
async def get_premium_plan_member():
    premium_plan_members = await PaymentsModel.find(
        PaymentsModel.subscription_name == "Premium Plan"
    ).count()

    total_user = await UserModel.find_all().count()

    return {
        "premium_plan_member": premium_plan_members,
        "total_user": total_user
    }