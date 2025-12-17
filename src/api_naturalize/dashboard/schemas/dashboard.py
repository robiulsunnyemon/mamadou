from typing import List
from pydantic import BaseModel
from api_naturalize.auth.schemas.user_schemas import UserResponse
from api_naturalize.progress_lesson.schemas.progress_lesson_schemas import FilteredLessonResponse
from enum import Enum

# Extended Dashboard Response Schema
class ExtendedDashboardResponse(BaseModel):
    total_score: int  # From LeaderBoard
    total_lessons: int
    success_rate: float
    average_score: float
    completed_lesson:int
    user_details: UserResponse
    in_progress_lessons: List[FilteredLessonResponse]



# Schema for question statistics
class QuestionStatisticsResponse(BaseModel):
    question_id: str
    question_name: str
    total_attempts: int
    wrong_attempts: int
    correct_attempts: int
    success_rate: float
    wrong_percentage: float


# Schema for most difficult questions
class MostDifficultQuestionsResponse(BaseModel):
    question_id: str
    question_name: str
    wrong_attempts: int
    success_rate: float
    lesson_name: str
    course_name: str




# Schema for user statistics
class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    suspended_users: int
    verified_users: int
    unverified_users: int


class MonthlyRegistrationResponse(BaseModel):
    year: int
    month: int
    month_name: str
    registrations: int


class UserGrowthResponse(BaseModel):
    period: str
    total_users: int
    new_users: int
    growth_rate: float


class UserStatusFilter(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPEND = "SUSPEND"
    ALL = "ALL"




