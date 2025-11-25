from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from mamadou.database.database import initialize_database, close_database
from mamadou.auth.routers.user_routes import router as auth_router
from mamadou.course.routers.course_routes import router as course_router
from mamadou.lesson.routers.lesson_routes import router as lesson_router
from mamadou.question.routers.question_routes import router as question_router



@asynccontextmanager
async def lifespan_context(_: FastAPI):
    await initialize_database()
    yield
    await close_database()

app = FastAPI(
    title="Mamadou Education Platform",
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

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Best wishes from Mamadou Education Development team"}



app.include_router(auth_router)
app.include_router(course_router)
app.include_router(lesson_router)
app.include_router(question_router)
