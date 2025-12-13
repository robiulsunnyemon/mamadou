from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from api_naturalize.database.database import initialize_database, close_database
from api_naturalize.auth.routers.auth_routers import router as auth_router
from api_naturalize.auth.routers.user_routes import user_router
from api_naturalize.frequent_question.routers.frequent_question_routes import router as frequent_question_router
from api_naturalize.course.routers.course_routes import router as course_router
from api_naturalize.lesson.routers.lesson_routes import router as lesson_router
from api_naturalize.question.routers.question_routes import router as question_router
from api_naturalize.answer.routers.answer_routes import router as answer_router
from api_naturalize.progress_lesson.routers.progress_lesson_routes import router as progress_lesson_router
from api_naturalize.leader_board.routers.leader_board_routes import router as leaderboard_router
from api_naturalize.dashboard.routers.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan_context(_: FastAPI):
    await initialize_database()
    yield
    await close_database()

app = FastAPI(
    title="Api_naturalize",
    description="Rest API",
    version="1.0.0",
    lifespan=lifespan_context,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["health"])
async def health():
    return {"message": "Api is working"}



app.include_router(auth_router,prefix="/api/v1")
app.include_router(user_router,prefix="/api/v1")
app.include_router(dashboard_router,prefix="/api/v1")
app.include_router(frequent_question_router,prefix="/api/v1")
app.include_router(course_router,prefix="/api/v1")
app.include_router(lesson_router,prefix="/api/v1")
app.include_router(question_router,prefix="/api/v1")
app.include_router(answer_router,prefix="/api/v1")
app.include_router(progress_lesson_router,prefix="/api/v1")
app.include_router(leaderboard_router,prefix="/api/v1")

