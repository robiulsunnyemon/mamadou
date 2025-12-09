# utils/token_generation.py
import os
from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timedelta, timezone
from src.api_naturalize.auth.models.user_model import UserModel

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')


async def create_access_token(user_id: str):
    """
    User ID নেয় এবং database থেকে user data নিয়ে JWT token তৈরি করে
    """
    # 1️⃣ Database থেকে user ডাটা fetch করুন
    user = await UserModel.find_one({"_id": user_id})

    if not user:
        raise ValueError("User not found")

    # 2️⃣ Token এর জন্য ডাটা prepare করুন
    token_data = {
        "sub": user.email,
        "user_id": str(user.id),  # ObjectId কে string এ convert
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "email": user.email,
        "is_verified": user.is_verified,
        "auth_provider": user.auth_provider if hasattr(user, 'auth_provider') else None
    }

    # 3️⃣ Expiry time add করুন
    expire = datetime.now(timezone.utc) + timedelta(days=90)
    token_data.update({"exp": expire})

    # 4️⃣ Token generate করুন
    encoded_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_token