from fastapi import APIRouter, HTTPException, status
from typing import List
from bson import ObjectId

from api_naturalize.course.models.course_model import CourseModel
from api_naturalize.lesson.models.lesson_model import LessonModel
from api_naturalize.question.models.question_model import QuestionModel
from api_naturalize.question.schemas.question_schemas import (
    QuestionCreate, 
    QuestionUpdate, 
    QuestionResponse,
    BulkQuestionResponse, 
    BulkQuestionCreate
)

router = APIRouter(prefix="/questions", tags=["questions"])


def convert_question_to_response(question: QuestionModel) -> dict:
    """Convert QuestionModel to response dict with proper id handling"""
    question_dict = question.model_dump()
    question_dict["id"] = str(question.id)
    return question_dict


# GET all questions
@router.get("/", response_model=List[QuestionResponse], status_code=status.HTTP_200_OK)
async def get_all_questions(skip: int = 0, limit: int = 10):
    """Get all questions with pagination"""
    questions = await QuestionModel.find_all().skip(skip).limit(limit).to_list()
    return [convert_question_to_response(q) for q in questions]


# GET question by ID
@router.get("/{id}", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def get_question(id: str):
    """Get question by ID"""
    try:
        question = await QuestionModel.get(ObjectId(id))
    except Exception:
        question = await QuestionModel.find_one(QuestionModel.id == id)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Question not found"
        )
    
    return convert_question_to_response(question)


# POST create new question
@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(question_data: QuestionCreate):
    """Create a new question"""
    # Validate course exists
    try:
        course = await CourseModel.get(ObjectId(question_data.course_id))
    except Exception:
        course = await CourseModel.find_one(CourseModel.id == question_data.course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Validate lesson exists
    try:
        lesson = await LessonModel.get(ObjectId(question_data.lesson_id))
    except Exception:
        lesson = await LessonModel.find_one(LessonModel.id == question_data.lesson_id)
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Create question
    question_dict = question_data.model_dump()
    question = QuestionModel(**question_dict)
    await question.create()
    
    return convert_question_to_response(question)


# PATCH update question
@router.patch("/{id}", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def update_question(id: str, question_data: QuestionUpdate):
    """Update question information"""
    try:
        question = await QuestionModel.get(ObjectId(id))
    except Exception:
        question = await QuestionModel.find_one(QuestionModel.id == id)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Question not found"
        )

    update_data = question_data.model_dump(exclude_unset=True)
    await question.update({"$set": update_data})
    
    # Fetch updated question
    try:
        updated_question = await QuestionModel.get(ObjectId(id))
    except Exception:
        updated_question = await QuestionModel.find_one(QuestionModel.id == id)
    
    return convert_question_to_response(updated_question)


# DELETE question
@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_question(id: str):
    """Delete question by ID"""
    try:
        question = await QuestionModel.get(ObjectId(id))
    except Exception:
        question = await QuestionModel.find_one(QuestionModel.id == id)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Question not found"
        )

    await question.delete()
    return {"message": "Question deleted successfully"}


# POST create bulk questions
@router.post("/bulk", response_model=BulkQuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_bulk_questions(bulk_data: BulkQuestionCreate):
    """Create multiple questions for different lesson IDs and course IDs"""
    created_questions = []

    # Validate all lesson IDs and course IDs first
    lesson_ids = {question.lesson_id for question in bulk_data.questions}
    course_ids = {question.course_id for question in bulk_data.questions}

    # Check if all lessons exist
    existing_lessons = {}
    for lesson_id in lesson_ids:
        try:
            lesson = await LessonModel.get(ObjectId(lesson_id))
        except Exception:
            lesson = await LessonModel.find_one(LessonModel.id == lesson_id)
        
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson with ID {lesson_id} not found"
            )
        existing_lessons[lesson_id] = lesson

    # Check if all courses exist
    existing_courses = {}
    for course_id in course_ids:
        try:
            course = await CourseModel.get(ObjectId(course_id))
        except Exception:
            course = await CourseModel.find_one(CourseModel.id == course_id)
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        existing_courses[course_id] = course

    # Validate that lessons belong to their respective courses
    for question_data in bulk_data.questions:
        lesson = existing_lessons[question_data.lesson_id]
        if str(lesson.course_id) != str(question_data.course_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lesson {question_data.lesson_id} does not belong to course {question_data.course_id}"
            )

    # Create all questions
    for question_data in bulk_data.questions:
        question_dict = question_data.model_dump()
        question = QuestionModel(**question_dict)
        await question.create()
        created_questions.append(convert_question_to_response(question))

    return BulkQuestionResponse(
        message="Questions created successfully",
        created_count=len(created_questions),
        questions=created_questions
    )


@router.delete("/delete/all", status_code=status.HTTP_200_OK)
async def all_question_delete():
    try:
        await QuestionModel.find_all().delete()

        return {
            "status": "success",
            "message": "All questions data has been deleted successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
        
        #  *** _ ***