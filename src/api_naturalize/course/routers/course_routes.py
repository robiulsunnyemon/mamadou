from fastapi import APIRouter, HTTPException
from typing import List

from fastapi.params import Depends

from api_naturalize.course.models.course_model import CourseModel
from api_naturalize.course.schemas.course_schemas import CourseCreate, CourseUpdate, CourseResponse, CourseResponseAdmin
from api_naturalize.lesson.models.lesson_model import LessonModel
from api_naturalize.progress_lesson.models.progress_lesson_model import ProgressLessonModel
from api_naturalize.question.models.question_model import QuestionModel
from api_naturalize.utils.user_info import get_user_info

router = APIRouter(prefix="/courses", tags=["courses"])



@router.get("/", response_model=List[CourseResponse])
async def get_all_courses(
    skip: int = 0,
    limit: int = 10,
    user_data: dict = Depends(get_user_info)
):
    user_id = user_data["user_id"]

    courses = await CourseModel.find_all().skip(skip).limit(limit).to_list()
    course_responses = []

    for course in courses:
        lessons = await LessonModel.find(
            LessonModel.course_id == course.id
        ).to_list()

        lesson_list = []
        total_lesson_progress=0

        for lesson in lessons:
            lesson_dict = lesson.model_dump()

            db_progress_lesson = await ProgressLessonModel.find_one(
                ProgressLessonModel.lesson_id == lesson.id,
                ProgressLessonModel.user_id == user_id
            )

            lesson_dict["my_progress"] = (
                db_progress_lesson.progress if db_progress_lesson else 0
            )

            total_lesson_progress+=lesson_dict["my_progress"]

            lesson_list.append(lesson_dict)

        total_questions = await QuestionModel.find(
            QuestionModel.course_id == course.id
        ).count()

        course_dict = course.model_dump()
        course_dict["lessons"] = lesson_list
        course_dict["total_questions"] = total_questions
        course_dict["course_progress"] = total_lesson_progress/len(lessons)

        course_responses.append(CourseResponse(**course_dict))

    return course_responses






@router.get("/fetch/admin", response_model=List[CourseResponseAdmin])
async def get_all_course(
    skip: int = 0,
    limit: int = 10
):

    courses = await CourseModel.find_all().skip(skip).limit(limit).to_list()

    return courses






# GET course by ID with nested lessons and total questions
@router.get("/{id}", response_model=CourseResponse)
async def get_course(id: str):
    """
    Get course by ID with nested lessons and total questions count
    """
    course = await CourseModel.get(id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Fetch lessons for this specific course
    lessons = await LessonModel.find(LessonModel.course_id == id).to_list()

    # Calculate total questions for this course
    total_questions = await QuestionModel.find(QuestionModel.course_id == id).count()

    # Convert course to dict and add nested data
    course_dict = course.model_dump()
    course_dict["lessons"] = lessons
    course_dict["total_questions"] = total_questions

    return CourseResponse(**course_dict)












# POST create new course
@router.post("/", response_model=CourseResponse)
async def create_course(course_data: CourseCreate):
    
    """
    Create a new course
    """
    course_dict = course_data.model_dump()
    course = CourseModel(**course_dict)
    await course.create()
    return course

# PATCH update course
@router.patch("/{id}", response_model=CourseResponse)
async def update_course(id: str, course_data: CourseUpdate):
    
    """
    Update course information
    """
    course = await CourseModel.get(id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = course_data.model_dump(exclude_unset=True)
    await course.update({"$set": update_data})
    return await CourseModel.get(id)

# DELETE course
@router.delete("/{id}")
async def delete_course(id: str):
    
    """
    Delete course by ID
    """
    course = await CourseModel.get(id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    await course.delete()
    return {"message": "Course deleted successfully"}


# Bulk create with custom response
@router.post("/bulk-create")
async def bulk_create_courses_with_custom_response(courses_data: List[CourseCreate]):
    """
    Create multiple courses with custom response including success count
    """
    if not courses_data:
        raise HTTPException(status_code=400, detail="No courses provided")

    success_count = 0
    failed_courses = []
    created_courses = []

    for course_data in courses_data:
        try:
            # Check for duplicates
            existing_course = await CourseModel.find_one(CourseModel.name == course_data.name)
            if existing_course:
                failed_courses.append({
                    "name": course_data.name,
                    "error": "Course with this name already exists"
                })
                continue

            course_dict = course_data.model_dump()
            course = CourseModel(**course_dict)
            await course.create()
            created_courses.append(course)
            success_count += 1

        except Exception as e:
            failed_courses.append({
                "name": course_data.name,
                "error": str(e)
            })

    return {
        "message": f"Bulk create completed. Success: {success_count}, Failed: {len(failed_courses)}",
        "success_count": success_count,
        "failed_count": len(failed_courses),
        "created_courses": created_courses,
        "failed_courses": failed_courses
    }