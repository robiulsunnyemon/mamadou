from fastapi import APIRouter, HTTPException,status
from typing import List

from fastapi.params import Depends

from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.frequent_question.models.frequent_question_model import FrequentQuestionModel
from api_naturalize.frequent_question.schemas.frequent_question_schemas import FrequentquestionCreate, FrequentquestionUpdate, FrequentquestionResponse
from api_naturalize.utils.user_info import get_user_info

router = APIRouter(prefix="/fqn", tags=["frequent_questions"])

# GET all frequent_questions
@router.get("/", response_model=List[FrequentquestionResponse],status_code=status.HTTP_200_OK)
async def get_all_frequent_questions(skip: int = 0, limit: int = 10):
    
    """
    Get all frequent_questions with pagination
    """
    frequent_questions = await FrequentQuestionModel.find_all().skip(skip).limit(limit).to_list()
    return frequent_questions

# GET frequent_question by ID
@router.get("/{id}", response_model=FrequentquestionResponse,status_code=status.HTTP_200_OK)
async def get_frequent_question(id: str):
    
    """
    Get frequent_question by ID
    """
    frequent_question = await FrequentQuestionModel.get(id)
    if not frequent_question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FrequentQuestion not found")
    return frequent_question

# POST create new frequent_question
@router.post("/", response_model=FrequentquestionResponse,status_code=status.HTTP_201_CREATED)
async def create_frequent_question(frequent_question_data: FrequentquestionCreate,user:dict=Depends(get_user_info)):
    
    """
    Create a new frequent_question
    """
    user_id=user["user_id"]
    db_user=await UserModel.get(user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    frequent_question = FrequentQuestionModel(
        user_id= user_id,
        question=frequent_question_data.question,
        answer= frequent_question_data.answer
    )
    await frequent_question.create()
    return frequent_question


# PATCH update frequent_question
@router.patch("/{id}", response_model=FrequentquestionResponse,status_code=status.HTTP_200_OK)
async def update_frequent_question(id: str, frequent_question_data: FrequentquestionUpdate):
    
    """
    Update frequent_question information
    """
    frequent_question = await FrequentQuestionModel.get(id)
    if not frequent_question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FrequentQuestion not found")

    update_data = frequent_question_data.model_dump(exclude_unset=True)
    await frequent_question.update({"$set": update_data})
    return await FrequentQuestionModel.get(id)

# DELETE frequent_question
@router.delete("/{id}",status_code=status.HTTP_200_OK)
async def delete_frequent_question(id: str):
    
    """
    Delete frequent_question by ID
    """
    frequent_question = await FrequentQuestionModel.get(id)
    if not frequent_question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FrequentQuestion not found")

    await frequent_question.delete()
    return {"message": "FrequentQuestion deleted successfully"}
