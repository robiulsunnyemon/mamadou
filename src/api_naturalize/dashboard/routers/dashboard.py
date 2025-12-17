from fastapi import APIRouter, HTTPException,status,File, UploadFile, Form,Request
from typing import List
from api_naturalize.answer.models.answer_model import AnswerModel
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.auth.schemas.user_schemas import UserResponse
from api_naturalize.course.models.course_model import CourseModel
from api_naturalize.course.schemas.course_schemas import CourseResponse, CourseResponseAdmin
from api_naturalize.dashboard.schemas.dashboard import ExtendedDashboardResponse, QuestionStatisticsResponse, \
    MostDifficultQuestionsResponse, UserStatsResponse, MonthlyRegistrationResponse, UserGrowthResponse, UserStatusFilter
from api_naturalize.leader_board.models.leader_board_model import LeaderBoardModel
from api_naturalize.lesson.models.lesson_model import LessonModel
from api_naturalize.lesson.schemas.lesson_schemas import LessonResponseAdmin, LessonRes
from api_naturalize.progress_lesson.models.progress_lesson_model import ProgressLessonModel
from api_naturalize.progress_lesson.schemas.progress_lesson_schemas import FilteredLessonResponse
from api_naturalize.question.models.question_model import QuestionModel
from datetime import datetime, timedelta,timezone
from api_naturalize.utils.account_status import AccountStatus
from api_naturalize.utils.user_role import UserRole
from pathlib import Path
from typing import Annotated
import shutil
import uuid
from fastapi.encoders import jsonable_encoder


UPLOAD_DIR = "uploaded_images"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])



@router.get("/course/all",response_model=List[CourseResponseAdmin],status_code=status.HTTP_200_OK)
async def get_all_course(
    skip: int = 0,
    limit: int = 10
):

    courses = await CourseModel.find_all().sort("-created_at").skip(skip).limit(limit).to_list()

    return courses


@router.post("/create/course", status_code=status.HTTP_201_CREATED)
async def create_course(
        request: Request,
        name: Annotated[str, Form()],
        description: Annotated[str, Form()],
        course_image: Annotated[UploadFile, File()]
):
    """
    Create a new course and upload its image
    """


    file_extension = Path(course_image.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = Path(UPLOAD_DIR) / unique_filename


    try:

        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(course_image.file, buffer)
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {e}"
        )


    base_url = str(request.base_url).replace("http://", "https://")
    image_url = f"{base_url}static/{unique_filename}"


    course_data = {
        "name": name,
        "description": description,
        "image_url": image_url

    }

    course = CourseModel(**course_data)
    await course.create()

    # Response
    return {"message": "Course created successfully", "course_data": course_data}


@router.get("/user/all", status_code=status.HTTP_200_OK)
async def get_all_user(
        skip: int = 0,
        limit: int = 10
):
    db_users = await UserModel.find_all().sort("-created_at").skip(skip).limit(limit).to_list()
    res = []

    for db_user in db_users:

        total_ans = await AnswerModel.find(
            AnswerModel.user_id == db_user.id
        ).count()

        total_r8_ans = await AnswerModel.find(
            (AnswerModel.user_id == db_user.id),
            (AnswerModel.score == 1)
        ).count()


        success_rate = 0
        if total_ans > 0:
            success_rate = (total_r8_ans / total_ans) * 100

        user_res = UserResponse(**db_user.model_dump())

        res.append({
            "user": user_res,
            "score": total_r8_ans,
            "success_rate": round(success_rate, 2),
            "subscription":"basic"
        })

    return res
















# POST create new lesson
@router.post("/create/lesson",status_code=status.HTTP_201_CREATED)
async def create_lesson(
        request: Request,
        name: Annotated[str, Form()],
        description: Annotated[str, Form()],
        image_url: Annotated[UploadFile, File()],
        course_id: Annotated[str, Form()],

):
    """
    Check Course id is valid?
    """

    db_course=await  CourseModel.get(course_id)
    if not db_course:
        raise  HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Course is not found")


    """
    Create a new lesson
    """


    file_extension = Path(image_url.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = Path(UPLOAD_DIR) / unique_filename


    try:

        with open(file_path, "wb") as buffer:

            shutil.copyfileobj(image_url.file, buffer)
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {e}"
        )


    base_url = str(request.base_url).replace("http://", "https://")
    image_url = f"{base_url}static/{unique_filename}"


    lesson_data = {
        "name": name,
        "description": description,
        "image_url": image_url,
        "course_id":course_id
    }




    lesson = LessonModel(**lesson_data)
    await lesson.create()
    return lesson















@router.get("/lesson/all",response_model=List[LessonResponseAdmin], status_code=status.HTTP_200_OK)
async def get_all_lesson(
    skip: int = 0,
    limit: int = 10
):

    lessons = await LessonModel.find_all().sort("-created_at").skip(skip).limit(limit).to_list()

    return lessons





# GET lesson by Course ID - simplified
@router.get("/lesson/by_course_id/{id}",response_model=List[LessonRes], status_code=status.HTTP_200_OK)
async def get_lesson(id: str):
    """
    Get lesson by ID
    """

    db_course=await CourseModel.get(id)
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")


    lessons = await LessonModel.find(LessonModel.course_id==id).to_list()

    return lessons



















@router.get("/users/{id}", response_model=ExtendedDashboardResponse)
async def get_extended_dashboard_stats(
        id: str,

):
    """
    Get extended dashboard statistics for a specific user including:
    - total_score from leaderboard
    - total_lessons
    - success_rate
    - user details
    - in-progress lessons (progress > 0 and < 100)
    """

    # Get user details
    user = await UserModel.get(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert user model to UserResponse
    user_response = UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        is_verified=user.is_verified,
        profile_image=user.profile_image,
        auth_provider=user.auth_provider,
        created_at=user.created_at,
        updated_at=user.updated_at,
        role=user.role,
        otp=user.otp,
        account_status=user.account_status
    )

    # Get total_score from LeaderBoardModel
    leaderboard_data = await LeaderBoardModel.find_one(LeaderBoardModel.user_id == id)
    total_score = leaderboard_data.total_score if leaderboard_data else 0

    # Get total lessons count
    total_lessons = await LessonModel.find_all().count()

    # Calculate success rate
    total_questions = await QuestionModel.find_all().count()
    success_rate = (total_questions * total_score) / 100 if total_questions > 0 else 0.0

    # Get in-progress lessons (progress > 0 and < 100)
    in_progress_lessons = await get_in_progress_lessons(id)

    completed_lesson = await ProgressLessonModel.find(
        ProgressLessonModel.user_id == id,
        ProgressLessonModel.progress == 100
    ).count()

    return ExtendedDashboardResponse(
        total_score=total_score,
        total_lessons=total_lessons,
        success_rate=success_rate,
        user_details=user_response,
        in_progress_lessons=in_progress_lessons,
        average_score=success_rate,
        completed_lesson=completed_lesson
    )

# Helper function to get in-progress lessons
async def get_in_progress_lessons(user_id: str) -> List[FilteredLessonResponse]:
    """
    Get lessons where user's progress is between 0 and 100 (exclusive)
    """
    # Get progress records where progress > 0 and < 100
    progress_records = await ProgressLessonModel.find(
        ProgressLessonModel.user_id == user_id,
        ProgressLessonModel.progress > 0,
        ProgressLessonModel.progress < 100
    ).to_list()

    in_progress_lessons = []

    for progress in progress_records:
        lesson = await LessonModel.get(progress.lesson_id)
        if not lesson:
            continue

        # Fetch questions for this lesson
        questions = await QuestionModel.find(QuestionModel.lesson_id == lesson.id).to_list()
        total_questions = len(questions)

        # Calculate total right answers for this user in this lesson
        user_answers = await AnswerModel.find(
            AnswerModel.user_id == user_id,
            AnswerModel.lesson_id == lesson.id
        ).to_list()
        total_right_answers = sum(1 for answer in user_answers if answer.score == 1)

        # Create filtered lesson response
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

        in_progress_lessons.append(filtered_lesson)

    return in_progress_lessons




# GET course by ID with nested lessons and total questions
@router.get("/courses/{id}", response_model=CourseResponse)
async def get_course(id: str):
    course_id=id
    """
    Get course by ID with nested lessons and total questions count
    """
    course = await CourseModel.get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Fetch lessons for this specific course
    lessons = await LessonModel.find(LessonModel.course_id == course_id).to_list()

    # Calculate total questions for this course
    total_questions = await QuestionModel.find(QuestionModel.course_id == course_id).count()

    # Convert course to dict and add nested data
    course_dict = course.model_dump()
    course_dict["lessons"] = lessons
    course_dict["total_questions"] = total_questions

    return CourseResponse(**course_dict)


# GET question statistics with filtering - FINAL FIXED VERSION
@router.get("/statistics/questions/", response_model=List[QuestionStatisticsResponse])
async def get_question_statistics(
        min_attempts: int = 1,
        min_wrong_percentage: float = 0.0,
        limit: int = 50
):
    """
    Get statistics for all questions with filtering options
    """
    # Get all answers
    all_answers = await AnswerModel.find_all().to_list()

    # Group answers by question_id manually
    question_stats = {}

    for answer in all_answers:
        question_id = answer.question_id

        if question_id not in question_stats:
            question_stats[question_id] = {
                "total_attempts": 0,
                "wrong_attempts": 0,
                "correct_attempts": 0
            }

        question_stats[question_id]["total_attempts"] += 1
        if answer.score == 0:
            question_stats[question_id]["wrong_attempts"] += 1
        else:
            question_stats[question_id]["correct_attempts"] += 1

    # Calculate percentages and filter
    result = []
    for question_id, stats in question_stats.items():
        if stats["total_attempts"] < min_attempts:
            continue

        success_rate = (stats["correct_attempts"] / stats["total_attempts"] * 100) if stats["total_attempts"] > 0 else 0
        wrong_percentage = (stats["wrong_attempts"] / stats["total_attempts"] * 100) if stats[
                                                                                            "total_attempts"] > 0 else 0

        if wrong_percentage < min_wrong_percentage:
            continue

        # Get question details
        question = await QuestionModel.get(question_id)

        if question:
            result.append(QuestionStatisticsResponse(
                question_id=question_id,
                question_name=question.name,
                total_attempts=stats["total_attempts"],
                wrong_attempts=stats["wrong_attempts"],
                correct_attempts=stats["correct_attempts"],
                success_rate=round(success_rate, 2),
                wrong_percentage=round(wrong_percentage, 2)
            ))

    # Sort by wrong percentage (descending) and limit
    result.sort(key=lambda x: x.wrong_percentage, reverse=True)
    return result[:limit]


# GET most difficult questions (highest wrong percentage) - FIXED VERSION
@router.get("/questions/statistics/most-difficult/", response_model=List[dict])
async def get_most_difficult_questions(
        limit: int = 20,
        min_attempts: int = 5
):
    """
    Get most difficult questions based on wrong answer percentage
    """
    all_answers = await AnswerModel.find_all().to_list()

    # Group by question_id
    question_stats = {}

    for answer in all_answers:
        question_id = answer.question_id

        if question_id not in question_stats:
            question_stats[question_id] = {
                "total_attempts": 0,
                "wrong_attempts": 0
            }

        question_stats[question_id]["total_attempts"] += 1
        if answer.score == 0:
            question_stats[question_id]["wrong_attempts"] += 1

    # Filter and calculate
    difficult_questions = []

    for question_id, stats in question_stats.items():
        if stats["total_attempts"] < min_attempts:
            continue

        success_rate = ((stats["total_attempts"] - stats["wrong_attempts"]) / stats["total_attempts"] * 100) if stats[
                                                                                                                    "total_attempts"] > 0 else 0

        # Get question, lesson, and course details
        question = await QuestionModel.get(question_id)
        if not question:
            continue

        lesson = await LessonModel.get(question.lesson_id)
        course = await CourseModel.get(question.course_id) if lesson else None

        difficult_questions.append({
            "question_id": question_id,
            "question_name": question.name,
            "wrong_attempts": stats["wrong_attempts"],
            "success_rate": round(success_rate, 2),
            "lesson_name": lesson.name if lesson else "Unknown Lesson",
            "course_name": course.name if course else "Unknown Course"
        })

    # Sort by wrong attempts (descending) and success rate (ascending)
    difficult_questions.sort(key=lambda x: (-x["wrong_attempts"], x["success_rate"]))
    return difficult_questions[:limit]


# Alternative using proper MongoDB aggregation
@router.get("/statistics/questions/aggregate/", response_model=List[QuestionStatisticsResponse])
async def get_question_statistics_aggregate(
        min_attempts: int = 1,
        min_wrong_percentage: float = 0.0,
        limit: int = 50
):
    """
    Get question statistics using proper aggregation
    """
    try:
        # Use Beanie's motor collection directly
        collection = AnswerModel.get_motor_collection()

        pipeline = [
            {
                "$group": {
                    "_id": "$question_id",
                    "total_attempts": {"$sum": 1},
                    "wrong_attempts": {"$sum": {"$cond": [{"$eq": ["$score", 0]}, 1, 0]}},
                    "correct_attempts": {"$sum": {"$cond": [{"$eq": ["$score", 1]}, 1, 0]}}
                }
            },
            {
                "$match": {
                    "total_attempts": {"$gte": min_attempts}
                }
            },
            {
                "$addFields": {
                    "success_rate": {
                        "$multiply": [
                            {"$divide": ["$correct_attempts", "$total_attempts"]},
                            100
                        ]
                    },
                    "wrong_percentage": {
                        "$multiply": [
                            {"$divide": ["$wrong_attempts", "$total_attempts"]},
                            100
                        ]
                    }
                }
            },
            {
                "$match": {
                    "wrong_percentage": {"$gte": min_wrong_percentage}
                }
            },
            {
                "$sort": {"wrong_percentage": -1}
            },
            {
                "$limit": limit
            }
        ]

        # Execute aggregation
        cursor = collection.aggregate(pipeline)
        stats_data = await cursor.to_list(length=limit)

        # Get question details and format response
        result = []
        for data in stats_data:
            question_id = data["_id"]
            question = await QuestionModel.get(question_id)

            if question:
                result.append(QuestionStatisticsResponse(
                    question_id=question_id,
                    question_name=question.name,
                    total_attempts=data["total_attempts"],
                    wrong_attempts=data["wrong_attempts"],
                    correct_attempts=data["correct_attempts"],
                    success_rate=round(data["success_rate"], 2),
                    wrong_percentage=round(data["wrong_percentage"], 2)
                ))

        return result

    except Exception as e:
        # Fallback to manual method if aggregation fails
        print(f"Aggregation failed: {e}")
        return await get_question_statistics(min_attempts, min_wrong_percentage, limit)


# GET overall statistics
@router.get("/statistics/overall/")
async def get_overall_statistics():
    """
    Get overall statistics for all answers
    """
    all_answers = await AnswerModel.find_all().to_list()

    total_answers = len(all_answers)
    wrong_answers = sum(1 for answer in all_answers if answer.score == 0)
    correct_answers = total_answers - wrong_answers

    overall_success_rate = (correct_answers / total_answers * 100) if total_answers > 0 else 0

    # Get unique questions and users
    unique_questions = len(set(answer.question_id for answer in all_answers))
    unique_users = len(set(answer.user_id for answer in all_answers))

    return {
        "total_answers": total_answers,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "overall_success_rate": round(overall_success_rate, 2),
        "unique_questions_attempted": unique_questions,
        "unique_users": unique_users,
        "average_success_rate": round(overall_success_rate, 2)
    }


# GET question performance by course
@router.get("/statistics/course/{course_id}")
async def get_question_statistics_by_course(course_id: str):
    """
    Get question statistics for a specific course
    """
    # Get all questions for this course
    course_questions = await QuestionModel.find(QuestionModel.course_id == course_id).to_list()

    course_stats = []
    for question in course_questions:
        # Get answers for this question
        question_answers = await AnswerModel.find(AnswerModel.question_id == question.id).to_list()

        total_attempts = len(question_answers)
        wrong_attempts = sum(1 for answer in question_answers if answer.score == 0)
        correct_attempts = total_attempts - wrong_attempts

        success_rate = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        wrong_percentage = (wrong_attempts / total_attempts * 100) if total_attempts > 0 else 0

        course_stats.append({
            "question_id": question.id,
            "question_name": question.name,
            "difficulty": question.difficulty,
            "total_attempts": total_attempts,
            "wrong_attempts": wrong_attempts,
            "correct_attempts": correct_attempts,
            "success_rate": round(success_rate, 2),
            "wrong_percentage": round(wrong_percentage, 2)
        })

    # Sort by wrong percentage (descending)
    course_stats.sort(key=lambda x: x["wrong_percentage"], reverse=True)

    return {
        "course_id": course_id,
        "total_questions": len(course_questions),
        "question_statistics": course_stats
    }








# GET overall user statistics
@router.get("/statistics/users/overview", response_model=UserStatsResponse)
async def get_user_statistics_overview():
    """
    Get overall user statistics
    """
    # Total users count
    total_users = await UserModel.find_all().count()

    # Users by account status
    active_users = await UserModel.find(UserModel.account_status == AccountStatus.ACTIVE).count()
    inactive_users = await UserModel.find(UserModel.account_status == AccountStatus.INACTIVE).count()
    suspended_users = await UserModel.find(UserModel.account_status == AccountStatus.SUSPEND).count()

    # Users by verification status
    verified_users = await UserModel.find(UserModel.is_verified == True).count()
    unverified_users = total_users - verified_users

    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        suspended_users=suspended_users,
        verified_users=verified_users,
        unverified_users=unverified_users
    )


# GET monthly user registrations
@router.get("/statistics/users/registrations/monthly", response_model=List[MonthlyRegistrationResponse])
async def get_monthly_registrations(months: int = 12):
    """
    Get monthly user registration statistics for last N months
    """
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=months * 30)

    # Get all users created in the date range
    users = await UserModel.find(
        UserModel.created_at >= start_date,
        UserModel.created_at <= end_date
    ).to_list()

    # Group by month and year
    monthly_data = {}
    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    for user in users:
        year = user.created_at.year
        month = user.created_at.month
        key = f"{year}-{month}"

        if key not in monthly_data:
            monthly_data[key] = {
                "year": year,
                "month": month,
                "count": 0
            }
        monthly_data[key]["count"] += 1

    # Convert to response format and sort by year, month
    result = []
    for key, data in monthly_data.items():
        result.append(MonthlyRegistrationResponse(
            year=data["year"],
            month=data["month"],
            month_name=month_names[data["month"]],
            registrations=data["count"]
        ))

    result.sort(key=lambda x: (x.year, x.month))
    return result[-months:]  # Return only requested number of months


# GET user growth statistics
@router.get("/statistics/users/growth", response_model=List[UserGrowthResponse])
async def get_user_growth_statistics(period: str = "monthly"):
    """
    Get user growth statistics (daily, weekly, monthly)
    """
    end_date = datetime.now(timezone.utc)

    if period == "daily":
        days = 30
        start_date = end_date - timedelta(days=days)
        users = await UserModel.find(
            UserModel.created_at >= start_date,
            UserModel.created_at <= end_date
        ).to_list()

        # Group by day
        growth_data = {}
        for i in range(days + 1):
            date = (end_date - timedelta(days=i)).date()
            growth_data[date] = 0

        for user in users:
            user_date = user.created_at.date()
            if user_date in growth_data:
                growth_data[user_date] += 1

        result = []
        total_so_far = 0
        for date, count in sorted(growth_data.items()):
            total_so_far += count
            growth_rate = (count / (total_so_far - count)) * 100 if (total_so_far - count) > 0 else 0

            result.append(UserGrowthResponse(
                period=date.strftime("%Y-%m-%d"),
                total_users=total_so_far,
                new_users=count,
                growth_rate=round(growth_rate, 2)
            ))

        return result[::-1]  # Reverse to show oldest first

    elif period == "weekly":
        weeks = 12
        growth_data = []

        for i in range(weeks):
            week_end = end_date - timedelta(weeks=i)
            week_start = week_end - timedelta(weeks=1)

            weekly_users = await UserModel.find(
                UserModel.created_at >= week_start,
                UserModel.created_at < week_end
            ).count()

            total_users_until_week = await UserModel.find(
                UserModel.created_at < week_end
            ).count()

            growth_rate = (weekly_users / (total_users_until_week - weekly_users)) * 100 if (
                                                                                                        total_users_until_week - weekly_users) > 0 else 0

            growth_data.append(UserGrowthResponse(
                period=f"Week {weeks - i}",
                total_users=total_users_until_week + weekly_users,
                new_users=weekly_users,
                growth_rate=round(growth_rate, 2)
            ))

        return growth_data[::-1]

    else:  # monthly
        months = 12
        growth_data = []

        for i in range(months):
            month_end = end_date.replace(day=1) - timedelta(days=1) if i > 0 else end_date
            month_start = (month_end.replace(day=1) - timedelta(days=1)).replace(day=1) if i > 0 else end_date.replace(
                day=1)

            monthly_users = await UserModel.find(
                UserModel.created_at >= month_start,
                UserModel.created_at <= month_end
            ).count()

            total_users_until_month = await UserModel.find(
                UserModel.created_at < month_start
            ).count()

            growth_rate = (monthly_users / (total_users_until_month - monthly_users)) * 100 if (
                                                                                                           total_users_until_month - monthly_users) > 0 else 0

            growth_data.append(UserGrowthResponse(
                period=month_start.strftime("%Y-%m"),
                total_users=total_users_until_month + monthly_users,
                new_users=monthly_users,
                growth_rate=round(growth_rate, 2)
            ))

        return growth_data[::-1]


# GET users with status filtering
@router.get("/statistics/users/filter", response_model=List[UserResponse])
async def get_users_by_status(
        status: UserStatusFilter = UserStatusFilter.ALL,
        skip: int = 0,
        limit: int = 50,
        verified_only: bool = False
):
    """
    Get users filtered by status with pagination
    """
    query = {}

    # Build query based on filters
    if status != UserStatusFilter.ALL:
        query["account_status"] = status.value

    if verified_only:
        query["is_verified"] = True

    # Execute query
    if query:
        users = await UserModel.find(query).skip(skip).limit(limit).to_list()
    else:
        users = await UserModel.find_all().skip(skip).limit(limit).to_list()

    # Convert to response format
    user_responses = []
    for user in users:
        user_responses.append(UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=user.phone_number,
            is_verified=user.is_verified,
            profile_image=user.profile_image,
            auth_provider=user.auth_provider,
            created_at=user.created_at,
            updated_at=user.updated_at,
            role=user.role,
            otp=user.otp,
            account_status=user.account_status
        ))

    return user_responses


# GET user activity statistics
@router.get("/statistics/users/activity")
async def get_user_activity_statistics(days: int = 30):
    """
    Get user activity statistics (recently active users)
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Users created in the period
    new_users = await UserModel.find(
        UserModel.created_at >= cutoff_date
    ).count()

    # Users updated in the period (indicating activity)
    active_users = await UserModel.find(
        UserModel.updated_at >= cutoff_date
    ).count()

    # Users with recent progress (if ProgressLessonModel exists)
    try:
        recent_progress_users = await ProgressLessonModel.find(
            ProgressLessonModel.updated_at >= cutoff_date
        ).distinct("user_id")
        users_with_recent_progress = len(recent_progress_users)
    except:
        users_with_recent_progress = 0

    return {
        "period_days": days,
        "new_registrations": new_users,
        "active_users": active_users,
        "users_with_recent_progress": users_with_recent_progress,
        "cutoff_date": cutoff_date
    }


# GET user demographics
@router.get("/statistics/users/demographics")
async def get_user_demographics():
    """
    Get user demographics statistics
    """
    total_users = await UserModel.find_all().count()

    # Users by auth provider
    email_users = await UserModel.find(UserModel.auth_provider == "email").count()
    google_users = await UserModel.find(UserModel.auth_provider == "google").count()
    facebook_users = await UserModel.find(UserModel.auth_provider == "facebook").count()

    # Users by role
    admin_users = await UserModel.find(UserModel.role == UserRole.ADMIN).count()
    regular_users = await UserModel.find(UserModel.role == UserRole.USER).count()

    # Recent vs old users (last 30 days vs older)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    recent_users = await UserModel.find(UserModel.created_at >= cutoff_date).count()
    old_users = total_users - recent_users

    return {
        "total_users": total_users,
        "by_auth_provider": {
            "email": email_users,
            "google": google_users,
            "facebook": facebook_users,
            "other": total_users - (email_users + google_users + facebook_users)
        },
        "by_role": {
            "admin": admin_users,
            "user": regular_users
        },
        "by_registration_age": {
            "recent_30_days": recent_users,
            "older_than_30_days": old_users
        }
    }




### dashboar


@router.get("/filter/course", status_code=status.HTTP_200_OK)
async def all_course(skip: int = 0, limit: int = 10):

    safe_skip = int(skip)
    safe_limit = int(limit)


    courses = await CourseModel.find_all().sort("-created_at").skip(safe_skip).limit(safe_limit).to_list()

    res = []
    for course in courses:

        db_lessons = await LessonModel.find(LessonModel.course_id == course.id).to_list()
        db_question = await QuestionModel.find(QuestionModel.course_id == course.id).to_list()


        res_dic = {
            "course": course,
            "lessons": db_lessons,
            "questions": db_question,
            "total_question": len(db_question),
            "total_lesson": len(db_lessons),
            "status": "published"
        }
        res.append(res_dic)


    encoded_res = jsonable_encoder(res)


    def clean_ids(obj):
        if isinstance(obj, list):
            return [clean_ids(i) for i in obj]
        if isinstance(obj, dict):

            if "_id" in obj:
                obj["id"] = str(obj["_id"])
                del obj["_id"]
            return {k: clean_ids(v) for k, v in obj.items()}
        return obj

    return clean_ids(encoded_res)





@router.get("/filter/lesson", status_code=status.HTTP_200_OK)
async def all_lessons(skip: int = 0, limit: int = 10):
    safe_skip = int(skip)
    safe_limit = int(limit)

    lessons = await LessonModel.find_all().sort("-created_at").skip(safe_skip).limit(safe_limit).to_list()

    res = []
    for lesson in lessons:
        db_course = await CourseModel.get(lesson.course_id)
        db_question = await QuestionModel.find(QuestionModel.lesson_id == lesson.id).to_list()

        res_dic = {
            "course": db_course,
            "lesson": lesson,
            "questions": db_question,
            "total_question": len(db_question),
            "status": "published"
        }
        res.append(res_dic)

    encoded_res = jsonable_encoder(res)

    def clean_ids(obj):
        if isinstance(obj, list):
            return [clean_ids(i) for i in obj]
        if isinstance(obj, dict):

            if "_id" in obj:
                obj["id"] = str(obj["_id"])
                del obj["_id"]
            return {k: clean_ids(v) for k, v in obj.items()}
        return obj

    return clean_ids(encoded_res)