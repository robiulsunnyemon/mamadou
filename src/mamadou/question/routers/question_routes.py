from fastapi import APIRouter, HTTPException,status
from typing import List
from mamadou.question.models.question_model import QuestionModel
from mamadou.question.schemas.question_schemas import QuestionCreate, QuestionUpdate, QuestionResponse

router = APIRouter(prefix="/questions", tags=["questions"])

# GET all questions
@router.get("/", response_model=List[QuestionResponse],status_code=status.HTTP_200_OK)
async def get_all_questions(skip: int = 0, limit: int = 10):
    
    """
    Get all questions with pagination
    """
    questions = await QuestionModel.find_all().skip(skip).limit(limit).to_list()
    return questions

# GET question by ID
@router.get("/{question_id}", response_model=QuestionResponse,status_code=status.HTTP_200_OK)
async def get_question(question_id: str):
    
    """
    Get question by ID
    """
    question = await QuestionModel.get(question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return question

# POST create new question
@router.post("/", response_model=QuestionResponse,status_code=status.HTTP_201_CREATED)
async def create_question(question_data: QuestionCreate):
    
    """
    Create a new question
    """
    question_dict = question_data.model_dump()
    question = QuestionModel(**question_dict)
    await question.create()
    return question

# PATCH update question
@router.patch("/{question_id}", response_model=QuestionResponse,status_code=status.HTTP_200_OK)
async def update_question(question_id: str, question_data: QuestionUpdate):
    
    """
    Update question information
    """
    question = await QuestionModel.get(question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    update_data = question_data.model_dump(exclude_unset=True)
    await question.update({"$set": update_data})
    return await QuestionModel.get(question_id)

# DELETE question
@router.delete("/{question_id}",status_code=status.HTTP_200_OK)
async def delete_question(question_id: str):
    
    """
    Delete question by ID
    """
    question = await QuestionModel.get(question_id)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    await question.delete()
    return {"message": "Question deleted successfully"}
