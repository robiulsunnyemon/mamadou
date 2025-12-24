from fastapi import APIRouter, HTTPException,status,Depends
from typing import List
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.time_storage.models.time_storage_model import TimeStorageModel
from api_naturalize.time_storage.schemas.time_storage_schemas import TimestorageCreate, TimestorageUpdate, TimestorageResponse
from api_naturalize.utils.user_info import get_user_info

router = APIRouter(prefix="/time", tags=["time_storages"])

# GET all time_storages
@router.get("/", response_model=List[TimestorageResponse],status_code=status.HTTP_200_OK)
async def get_all_time_storages(skip: int = 0, limit: int = 10):
    
    """
    Get all time_storages with pagination
    """
    time_storages = await TimeStorageModel.find_all().skip(skip).limit(limit).to_list()
    return time_storages

# GET time_storage by ID
@router.get("/{time_storage_id}", response_model=TimestorageResponse,status_code=status.HTTP_200_OK)
async def get_time_storage(time_storage_id: str):
    
    """
    Get time_storage by ID
    """
    time_storage = await TimeStorageModel.get(time_storage_id)
    if not time_storage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TimeStorage not found")
    return time_storage


# GET time_storage by ID
@router.get("/user/{user_id}", response_model=TimestorageResponse, status_code=status.HTTP_200_OK)
async def get_time_storage(user_id:str):
    """
    Get time_storage by ID
    """
    db_user = await  UserModel.get(user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    time_storage = await TimeStorageModel.find_one(TimeStorageModel.user_id==db_user.id)
    if not time_storage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TimeStorage not found")
    return time_storage



# POST create new time_storage
@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_time_storage(time_storage_data: TimestorageCreate,user:dict=Depends(get_user_info)):
    
    """
    Create a new time_storage
    """
    db_user=await  UserModel.get(user["user_id"])
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User does not exist")

    db_time_storage=await TimeStorageModel.find_one(TimeStorageModel.user_id==db_user.id)
    if not db_time_storage:
        time_storage_dict = time_storage_data.model_dump()
        time_storage_dict["user_id"]=db_user.id
        time_storage = TimeStorageModel(**time_storage_dict)
        await time_storage.insert()
    else:
        db_time_storage.total_time += time_storage_data.total_time
        await db_time_storage.save()

    return {"message":"successfully saved time"}

# PATCH update time_storage
@router.patch("/{time_storage_id}", response_model=TimestorageResponse,status_code=status.HTTP_200_OK)
async def update_time_storage(time_storage_id: str, time_storage_data: TimestorageUpdate):
    
    """
    Update time_storage information
    """
    time_storage = await TimeStorageModel.get(time_storage_id)
    if not time_storage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TimeStorage not found")

    update_data = time_storage_data.model_dump(exclude_unset=True)
    await time_storage.update({"$set": update_data})
    return await TimeStorageModel.get(time_storage_id)

# DELETE time_storage
@router.delete("/{time_storage_id}",status_code=status.HTTP_200_OK)
async def delete_time_storage(time_storage_id: str):
    
    """
    Delete time_storage by ID
    """
    time_storage = await TimeStorageModel.get(time_storage_id)
    if not time_storage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TimeStorage not found")

    await time_storage.delete()
    return {"message": "TimeStorage deleted successfully"}
