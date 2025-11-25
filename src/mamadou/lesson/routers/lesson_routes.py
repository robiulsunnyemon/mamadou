from fastapi import APIRouter, HTTPException,status
from typing import List
from mamadou.lesson.models.lesson_model import LessonModel
from mamadou.lesson.schemas.lesson_schemas import LessonCreate, LessonUpdate, LessonResponse
from mamadou.course.models.course_model import CourseModel



router = APIRouter(prefix="/lessons", tags=["lessons"])

# GET all lessons
@router.get("/", response_model=List[LessonResponse],status_code=status.HTTP_200_OK)
async def get_all_lessons(skip: int = 0, limit: int = 10):
    
    """
    Get all lessons with pagination
    """
    lessons = await LessonModel.find_all().skip(skip).limit(limit).to_list()
    return lessons

# GET lesson by ID
@router.get("/{lesson_id}", response_model=LessonResponse,status_code=status.HTTP_200_OK)
async def get_lesson(lesson_id: str):
    
    """
    Get lesson by ID
    """
    lesson = await LessonModel.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

# POST create new lesson
@router.post("/", response_model=LessonResponse,status_code=status.HTTP_201_CREATED)
async def create_lesson(lesson_data: LessonCreate):
    """
    Check Course id is valid?
    """

    db_course=await  CourseModel.get(lesson_data.course_id)
    if not db_course:
        raise  HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Course is not found")


    """
    Create a new lesson
    """
    lesson_dict = lesson_data.model_dump()
    lesson = LessonModel(**lesson_dict)
    await lesson.create()
    return lesson

# PATCH update lesson
@router.patch("/{lesson_id}", response_model=LessonResponse,status_code=status.HTTP_200_OK)
async def update_lesson(lesson_id: str, lesson_data: LessonUpdate):
    
    """
    Update lesson information
    """
    lesson = await LessonModel.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    update_data = lesson_data.model_dump(exclude_unset=True)
    await lesson.update({"$set": update_data})
    return await LessonModel.get(lesson_id)

# DELETE lesson
@router.delete("/{lesson_id}",status_code=status.HTTP_200_OK)
async def delete_lesson(lesson_id: str):
    
    """
    Delete lesson by ID
    """
    lesson = await LessonModel.get(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    await lesson.delete()
    return {"message": "Lesson deleted successfully"}
