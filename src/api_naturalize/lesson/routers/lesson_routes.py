from fastapi import APIRouter, HTTPException,status
from typing import List

from fastapi.params import Depends

from api_naturalize.answer.models.answer_model import AnswerModel
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.lesson.models.lesson_model import LessonModel
from api_naturalize.lesson.schemas.lesson_schemas import LessonCreate, LessonUpdate, LessonResponse, BulkLessonResponse, \
    BulkLessonCreate
from api_naturalize.course.models.course_model import CourseModel
from api_naturalize.progress_lesson.models.progress_lesson_model import ProgressLessonModel
from api_naturalize.question.models.question_model import QuestionModel
from api_naturalize.utils.user_info import get_user_info

router = APIRouter(prefix="/lessons", tags=["lessons"])



# GET all lessons without user dependency
@router.get("/", response_model=List[LessonResponse], status_code=status.HTTP_200_OK)
async def get_all_lessons_public(
        skip: int = 0,
        limit: int = 10
):
    """
    Get all lessons with pagination and questions (without user progress)
    """
    lessons = await LessonModel.find_all().sort("-created_at").skip(skip).limit(limit).to_list()

    lesson_responses = []
    for lesson in lessons:
        # Fetch questions for this lesson
        questions = await QuestionModel.find(QuestionModel.lesson_id == lesson.id).to_list()
        total_questions = len(questions)

        # Convert lesson to dict and add nested data
        lesson_dict = lesson.dict()
        lesson_dict["questions"] = questions
        lesson_dict["my_progress"] = 0.0  # Default 0 for public access
        lesson_dict["total_right_answers"] = 0  # Default 0 for public access
        lesson_dict["total_questions"] = total_questions

        lesson_responses.append(LessonResponse(**lesson_dict))

    return lesson_responses




# GET lesson by ID - simplified
@router.get("/{id}", response_model=LessonResponse, status_code=status.HTTP_200_OK)
async def get_lesson(id: str, user: dict = Depends(get_user_info)):
    """
    Get lesson by ID with simplified progress
    """
    user_id = user["user_id"]
    db_user = await UserModel.get(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    lesson = await LessonModel.get(id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Fetch questions for this specific lesson
    questions = await QuestionModel.find(QuestionModel.lesson_id == id).to_list()
    total_questions = len(questions)

    # Calculate progress percentage
    my_progress = 0.0
    if user_id:
        progress_data = await ProgressLessonModel.find_one(
            ProgressLessonModel.lesson_id == id,
            ProgressLessonModel.user_id == user_id
        )
        if progress_data:
            my_progress = progress_data.progress  # Directly get the progress percentage

    # Calculate total right answers for this user in this lesson
    total_right_answers = 0
    if user_id:
        # Corrected query syntax for Beanie ODM
        user_answers = await AnswerModel.find(
            AnswerModel.user_id == user_id,
            AnswerModel.lesson_id == id
        ).to_list()

        total_right_answers = sum(1 for answer in user_answers if answer.score == 1)

    # Convert lesson to dict and add nested data
    lesson_dict = lesson.model_dump()
    lesson_dict["questions"] = questions
    lesson_dict["my_progress"] = my_progress  # Only progress percentage
    lesson_dict["total_right_answers"] = total_right_answers
    lesson_dict["total_questions"] = total_questions

    return LessonResponse(**lesson_dict)






# POST create new lesson
@router.post("/",status_code=status.HTTP_201_CREATED)
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
@router.patch("/{id}",status_code=status.HTTP_200_OK)
async def update_lesson(id: str, lesson_data: LessonUpdate):
    
    """
    Update lesson information
    """
    lesson = await LessonModel.get(id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    update_data = lesson_data.model_dump(exclude_unset=True)
    await lesson.update({"$set": update_data})
    return await LessonModel.get(id)

# DELETE lesson
@router.delete("/{id}",status_code=status.HTTP_200_OK)
async def delete_lesson(id: str):
    
    """
    Delete lesson by ID
    """
    lesson = await LessonModel.get(id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    await lesson.delete()
    return {"message": "Lesson deleted successfully"}










# POST create bulk lessons
@router.post("/bulk", response_model=BulkLessonResponse, status_code=status.HTTP_201_CREATED)
async def create_bulk_lessons(bulk_data: BulkLessonCreate):
    """
    Create multiple lessons for different course IDs
    """
    created_lessons = []

    # Validate all course IDs first
    course_ids = {lesson.course_id for lesson in bulk_data.lessons}
    existing_courses = {}

    for course_id in course_ids:
        course = await CourseModel.get(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found"
            )
        existing_courses[course_id] = course

    # Create all lessons
    for lesson_data in bulk_data.lessons:
        lesson_dict = lesson_data.model_dump()
        lesson = LessonModel(**lesson_dict)
        await lesson.create()
        created_lessons.append(lesson)

    return BulkLessonResponse(
        message="Lessons created successfully",
        created_count=len(created_lessons),
        lessons=created_lessons
    )
