from fastapi import APIRouter, HTTPException
from typing import List
from mamadou.course.models.course_model import CourseModel
from mamadou.course.schemas.course_schemas import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/courses", tags=["courses"])

# GET all courses
@router.get("/", response_model=List[CourseResponse])
async def get_all_courses(skip: int = 0, limit: int = 10):
    
    """
    Get all courses with pagination
    """
    courses = await CourseModel.find_all().skip(skip).limit(limit).to_list()
    return courses

# GET course by ID
@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: str):
    
    """
    Get course by ID
    """
    course = await CourseModel.get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

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
@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(course_id: str, course_data: CourseUpdate):
    
    """
    Update course information
    """
    course = await CourseModel.get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = course_data.model_dump(exclude_unset=True)
    await course.update({"$set": update_data})
    return await CourseModel.get(course_id)

# DELETE course
@router.delete("/{course_id}")
async def delete_course(course_id: str):
    
    """
    Delete course by ID
    """
    course = await CourseModel.get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    await course.delete()
    return {"message": "Course deleted successfully"}
