from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from api_naturalize.database.database import initialize_database, close_database
from api_naturalize.auth.routers.auth_routers import router as auth_router
from api_naturalize.auth.routers.user_routes import router
from api_naturalize.frequent_question.routers.frequent_question_routes import router as frequent_question_router
from api_naturalize.course.routers.course_routes import router as course_router
from api_naturalize.lesson.routers.lesson_routes import router as lesson_router
from api_naturalize.question.routers.question_routes import router as question_router
from api_naturalize.answer.routers.answer_routes import router as answer_router
from api_naturalize.payments.routers.payments_routes import router as payment_router
from api_naturalize.progress_lesson.routers.progress_lesson_routes import router as progress_lesson_router
from api_naturalize.leader_board.routers.leader_board_routes import router as leaderboard_router
from api_naturalize.dashboard.routers.dashboard import router as dashboard_router
from api_naturalize.time_storage.routers.time_storage_routes import router as time_storage_router
from api_naturalize.notification.routers.notification_routes import router as notification_router
from api_naturalize.subscription_plan.routers.subscription_plan_routes import router as subscription_router
from api_naturalize.upload.routes import upload_routes


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

# Create directories if they don't exist
STATIC_DIR = Path("static")
UPLOADED_IMAGES_DIR = Path("uploaded_images")

# Create directories with proper permissions
STATIC_DIR.mkdir(exist_ok=True, parents=True)
UPLOADED_IMAGES_DIR.mkdir(exist_ok=True, parents=True)

# Set proper permissions (readable and writable)
try:
    os.chmod(STATIC_DIR, 0o755)
    os.chmod(UPLOADED_IMAGES_DIR, 0o755)
    print(f"✅ Directories created with proper permissions:")
    print(f"   - {STATIC_DIR.absolute()}")
    print(f"   - {UPLOADED_IMAGES_DIR.absolute()}")
except Exception as e:
    print(f"⚠️ Warning: Could not set directory permissions: {e}")

# Mount static files BEFORE routes
# This is critical - static mounts must come before route includes
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploaded_images", StaticFiles(directory=str(UPLOADED_IMAGES_DIR)), name="uploaded_images")

# CORS
origins = [
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:3000",
    "https://mamadou.mtscorporate.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
async def health():
    return {
        "message": "Api is working",
        "status": "healthy",
        "static_dir": str(STATIC_DIR.absolute()),
        "uploaded_images_dir": str(UPLOADED_IMAGES_DIR.absolute())
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check"""
    # Check if directories are writable
    static_writable = os.access(STATIC_DIR, os.W_OK)
    uploaded_writable = os.access(UPLOADED_IMAGES_DIR, os.W_OK)
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected",
        "static_files": "enabled",
        "directories": {
            "static": {
                "path": str(STATIC_DIR.absolute()),
                "exists": STATIC_DIR.exists(),
                "writable": static_writable
            },
            "uploaded_images": {
                "path": str(UPLOADED_IMAGES_DIR.absolute()),
                "exists": UPLOADED_IMAGES_DIR.exists(),
                "writable": uploaded_writable
            }
        }
    }

# Include routers AFTER static mounts
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(router, prefix="/api/v1", tags=["users"])
app.include_router(dashboard_router, prefix="/api/v1", tags=["dashboard"])
app.include_router(frequent_question_router, prefix="/api/v1", tags=["frequent_questions"])
app.include_router(course_router, prefix="/api/v1", tags=["courses"])
app.include_router(lesson_router, prefix="/api/v1", tags=["lessons"])
app.include_router(question_router, prefix="/api/v1", tags=["questions"])
app.include_router(answer_router, prefix="/api/v1", tags=["answers"])
app.include_router(progress_lesson_router, prefix="/api/v1", tags=["progress"])
app.include_router(leaderboard_router, prefix="/api/v1", tags=["leaderboard"])
app.include_router(time_storage_router, prefix="/api/v1", tags=["time_storage"])
app.include_router(notification_router, prefix="/api/v1", tags=["notifications"])
app.include_router(payment_router, prefix="/api/v1", tags=["payments"])
app.include_router(subscription_router, prefix="/api/v1", tags=["subscriptions"])

# Upload router
app.include_router(
    upload_routes.router,
    prefix="/api/v1",
    tags=["upload"]
)

print("FastAPI application initialized successfully")
print(f"Static files: {STATIC_DIR.absolute()}")
print(f"Uploaded images: {UPLOADED_IMAGES_DIR.absolute()}")

#   *** _ ***   