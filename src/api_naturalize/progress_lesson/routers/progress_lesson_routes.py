from fastapi import APIRouter, HTTPException,status,Depends
from typing import List
from api_naturalize.answer.models.answer_model import AnswerModel
from api_naturalize.leader_board.models.leader_board_model import LeaderBoardModel
from api_naturalize.lesson.models.lesson_model import LessonModel
from api_naturalize.progress_lesson.models.progress_lesson_model import ProgressLessonModel
from api_naturalize.progress_lesson.schemas.progress_lesson_schemas import ProgresslessonCreate, ProgresslessonUpdate, \
    ProgresslessonResponse, FilteredLessonResponse, DashboardStatsResponse
from api_naturalize.question.models.question_model import QuestionModel
from api_naturalize.utils.user_info import get_user_info

router = APIRouter(prefix="/progress", tags=["progress_lessons"])

# GET all progress_lessons
@router.get("/", response_model=List[ProgresslessonResponse],status_code=status.HTTP_200_OK)
async def get_all_progress_lessons(skip: int = 0, limit: int = 10):
    
    """
    Get all progress_lessons with pagination
    """
    progress_lessons = await ProgressLessonModel.find_all().skip(skip).limit(limit).to_list()
    return progress_lessons

# GET progress_lesson by ID
@router.get("/{id}", response_model=ProgresslessonResponse,status_code=status.HTTP_200_OK)
async def get_progress_lesson(id: str):
    
    """
    Get progress_lesson by ID
    """
    progress_lesson = await ProgressLessonModel.get(id)
    if not progress_lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ProgressLesson not found")
    return progress_lesson

# POST create new progress_lesson
@router.post("/", response_model=ProgresslessonResponse,status_code=status.HTTP_201_CREATED)
async def create_progress_lesson(progress_lesson_data: ProgresslessonCreate):
    
    """
    Create a new progress_lesson
    """
    progress_lesson_dict = progress_lesson_data.model_dump()
    progress_lesson = ProgressLessonModel(**progress_lesson_dict)
    await progress_lesson.create()
    return progress_lesson

# PATCH update progress_lesson
@router.patch("/{id}", response_model=ProgresslessonResponse,status_code=status.HTTP_200_OK)
async def update_progress_lesson(id: str, progress_lesson_data: ProgresslessonUpdate):
    
    """
    Update progress_lesson information
    """
    progress_lesson = await ProgressLessonModel.get(id)
    if not progress_lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ProgressLesson not found")

    update_data = progress_lesson_data.model_dump(exclude_unset=True)
    await progress_lesson.update({"$set": update_data})
    return await ProgressLessonModel.get(id)

# DELETE progress_lesson
@router.delete("/{id}",status_code=status.HTTP_200_OK)
async def delete_progress_lesson(id: str):
    
    """
    Delete progress_lesson by ID
    """
    progress_lesson = await ProgressLessonModel.get(id)
    if not progress_lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ProgressLesson not found")

    await progress_lesson.delete()
    return {"message": "ProgressLesson deleted successfully"}


# GET lessons by progress range
@router.get("/filter/", response_model=List[FilteredLessonResponse])
async def get_lessons_by_progress_range(
        user: dict = Depends(get_user_info),
        min_progress: float = 0.0,
        max_progress: float = 100.0,
        skip: int = 0,
        limit: int = 10
):
    """
    Get lessons where user's progress is between min_progress and max_progress
    Example:
    - /lessons/progress/filter/?min_progress=1&max_progress=50 (1% to 50%)
    - /lessons/progress/filter/?min_progress=0&max_progress=0 (not started lessons)
    - /lessons/progress/filter/?min_progress=100&max_progress=100 (completed lessons)
    """
    user_id = user["user_id"]

    # Validate progress range
    if min_progress < 0 or max_progress > 100 or min_progress > max_progress:
        raise HTTPException(
            status_code=400,
            detail="Invalid progress range. min_progress must be >= 0, max_progress <= 100, and min_progress <= max_progress"
        )

    # Get all progress records for this user within the range
    progress_records = await ProgressLessonModel.find(
        ProgressLessonModel.user_id == user_id,
        ProgressLessonModel.progress >= min_progress,
        ProgressLessonModel.progress <= max_progress
    ).skip(skip).limit(limit).to_list()

    if not progress_records:
        return []

    # Get lessons and their details
    filtered_lessons = []
    for progress in progress_records:
        lesson = await LessonModel.get(progress.lesson_id)
        if not lesson:
            continue

        # Fetch questions for this lesson
        questions = await QuestionModel.find(QuestionModel.lesson_id == lesson.id).to_list()
        total_questions = len(questions)

        # Calculate total right answers
        user_answers = await AnswerModel.find(
            AnswerModel.user_id == user_id,
            AnswerModel.lesson_id == lesson.id
        ).to_list()
        total_right_answers = sum(1 for answer in user_answers if answer.score == 1)

        filtered_lesson = FilteredLessonResponse(
            id=lesson.id,
            name=lesson.name,
            description=lesson.description,
            image_url=lesson.image_url,
            course_id=lesson.course_id,
            my_progress=progress.progress,
            total_right_answers=total_right_answers,
            total_questions=total_questions,
            created_at=lesson.created_at,
            updated_at=lesson.updated_at
        )
        filtered_lessons.append(filtered_lesson)

    return filtered_lessons


# GET dashboard statistics
@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(user: dict = Depends(get_user_info)):
    """
    Get dashboard statistics: total questions, total lessons, and success rate
    """
    user_id = user["user_id"]

    # Get total questions count
    total_questions = await QuestionModel.find_all().count()

    # Get total lessons count
    total_lessons = await LessonModel.find_all().count()

    # Calculate success rate using LeaderBoardModel
    leaderboard_data = await LeaderBoardModel.find_one(LeaderBoardModel.user_id == user_id)

    if leaderboard_data:
        total_score = leaderboard_data.total_score
        success_rate = (total_questions * total_score) / 100
    else:
        # If no leaderboard data found, success rate is 0
        success_rate = 0.0

    return DashboardStatsResponse(
        total_questions=total_questions,
        total_lessons=total_lessons,
        success_rate=success_rate
    )