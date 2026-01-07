from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from api_naturalize.answer.models.answer_model import AnswerModel
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.course.models.course_model import CourseModel
from api_naturalize.frequent_question.models.frequent_question_model import FrequentQuestionModel
from api_naturalize.leader_board.models.leader_board_model import LeaderBoardModel
from api_naturalize.lesson.models.lesson_model import LessonModel
from api_naturalize.notification.models.notification_model import notificationModel
from api_naturalize.payments.models.payments_model import PaymentsModel
from api_naturalize.progress_lesson.models.progress_lesson_model import ProgressLessonModel
from api_naturalize.question.models.question_model import QuestionModel
from api_naturalize.subscription_plan.models.subscription_plan_model import SubscriptionPlanModel
from api_naturalize.time_storage.models.time_storage_model import TimeStorageModel

# MongoDB connection settings
# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "mamadou")


client: Optional[AsyncIOMotorClient] = None


async def initialize_database():
    """
    Initialize MongoDB and Beanie ODM
    """
    global client
    client = AsyncIOMotorClient(MONGODB_URL)

    await init_beanie(
        database=client[DATABASE_NAME],
        document_models=[
            UserModel,
            FrequentQuestionModel,
            CourseModel,
            LessonModel,
            QuestionModel,
            AnswerModel,
            ProgressLessonModel,
            LeaderBoardModel,
            TimeStorageModel,
            notificationModel,
            PaymentsModel,
            SubscriptionPlanModel
        ],
    )

    print(f"✅ Connected to MongoDB database: {DATABASE_NAME}")


async def close_database():
    """
    Close MongoDB connection
    """
    global client
    if client:
        client.close()
        print("👋 MongoDB connection closed.")

def get_database():
    """
    Return MongoDB database instance
    """
    if client is None:
        raise RuntimeError("Database not initialized. Call initialize_database first.")
    return client[DATABASE_NAME]