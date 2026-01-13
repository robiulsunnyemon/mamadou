import os

def create_auth_structure():
    # Main folder
    main_folder = "auth"
    os.makedirs(main_folder, exist_ok=True)

    # Subfolders
    folders = ["models", "schemas", "routers"]
    for folder in folders:
        os.makedirs(os.path.join(main_folder, folder), exist_ok=True)

    # models/user_model.py
    model_content = '''from beanie import Document, before_event, Replace, Save
from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

from api_naturalize.utils.user_role import UserRole


class UserModel(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_verified: bool = False
    otp: Optional[str] = None
    role: Optional[UserRole] = Field(default=UserRole.USER)
    profile_image: Optional[str] = Field(default="https://cdn.pixabay.com/photo/2017/06/13/12/54/profile-2398783_1280.png")
    auth_provider: str =  Field(default="email")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Auto-update "updated_at" on update
    @before_event([Save, Replace])
    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = "users"


'''

    with open(os.path.join(main_folder, "models", "user_model.py"), "w", encoding='utf-8') as f:
        f.write(model_content)

    # schemas/user_schemas.py
    schema_content = '''from pydantic import BaseModel, EmailStr,Field
from typing import Optional
from datetime import datetime

from api_naturalize.utils.user_role import UserRole


class UserCreate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    phone_number: Optional[str]
    password: Optional[str] = None
    auth_provider: str = "email"


class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    profile_image: Optional[str]


class UserResponse(BaseModel):
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    phone_number: Optional[str]
    is_verified: bool
    profile_image: Optional[str]
    auth_provider: str
    created_at: datetime
    updated_at: datetime
    role: Optional[UserRole] = Field(default=UserRole.USER)
    otp:Optional[str]

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

'''

    with open(os.path.join(main_folder, "schemas", "user_schemas.py"), "w", encoding='utf-8') as f:
        f.write(schema_content)

    # routers/user_routes.py
    router_content = '''from fastapi import APIRouter, HTTPException, Depends,status
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.auth.schemas.user_schemas import UserCreate, UserUpdate, UserResponse, VerifyOTP
from api_naturalize.utils.email_config import SendOtpModel
from api_naturalize.utils.get_hashed_password import get_hashed_password,verify_password
from api_naturalize.utils.otp_generate import generate_otp
from api_naturalize.utils.token_generation import create_access_token

router = APIRouter(prefix="/users", tags=["users"])


# GET all users
@router.get("/", response_model=List[UserResponse],status_code=status.HTTP_200_OK)
async def get_all_users(skip: int = 0, limit: int = 10):
    """
    Get all users with pagination
    """
    users = await UserModel.find_all().skip(skip).limit(limit).to_list()
    return users


# GET user by ID
@router.get("/{user_id}", response_model=UserResponse,status_code=status.HTTP_200_OK)
async def get_user(user_id: str):
    """
    Get user by ID
    """
    user = await UserModel.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# POST create new user
@router.post("/" ,response_model=UserResponse,status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    hashed_password = get_hashed_password(user.password)
    db_user = await UserModel.find_one(UserModel.email == user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    otp = generate_otp()
    new_user = UserModel(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        password=hashed_password,
        otp=otp
    )
    await new_user.insert()
    send_otp_data = SendOtpModel(email=new_user.email, otp=new_user.otp)
    ##await send_otp(send_otp_data)
    return new_user


# PATCH update user
@router.patch("/{user_id}", response_model=UserResponse,status_code=status.HTTP_200_OK)
async def update_user(user_id: str, user_data: UserUpdate):
    """
    Update user information
    """
    user = await UserModel.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    await user.update({"$set": update_data})
    return await UserModel.get(user_id)


# DELETE user
@router.delete("/{user_id}",status_code=status.HTTP_200_OK)
async def delete_user(user_id: str):
    """
    Delete user by ID
    """
    user = await UserModel.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user.delete()
    return {"message": "User deleted successfully"}
    

@router.post("/otp_verify", status_code=status.HTTP_200_OK)
async def verify_otp(user:VerifyOTP):
    db_user =await UserModel.find_one(UserModel.email == user.email)
    if db_user is None :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    if user.otp != db_user.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Wrong OTP")

    db_user.is_verified=True
    await db_user.save()
    return {"message":"You have  verified","data":db_user}


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db_user = await UserModel.find_one(
        {"$or": [{"email": form_data.username}, {"phone_number": form_data.username}]}
    )

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(form_data.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong password")

    if not db_user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your account is not verified with OTP")

    token = create_access_token(data={"sub": db_user.email, "role": db_user.role.value, "user_id": db_user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/resend_otp", status_code=status.HTTP_200_OK)
async def resend_otp(email:str):
    db_user = await UserModel.find_one(UserModel.email == email)
    if db_user is None :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    otp=generate_otp()
    db_user.otp=otp
    await db_user.save()
    send_otp_data = SendOtpModel(email=db_user.email, otp=db_user.otp)
    ##await send_otp(send_otp_data)
    return {
        "message": "User registered successfully.Please check your email.A 6 digit otp has been sent.",
        "data":db_user,
        "otp":db_user.otp
    }


@router.post("/reset_password", status_code=status.HTTP_200_OK)
async def reset_password(new_password:str,email:str):
    db_user = await UserModel.find_one(UserModel.email == email)
    if db_user is None :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")

    if not db_user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Your account is not verified with otp")

    hashed_password = get_hashed_password(new_password)
    db_user.password = hashed_password
    await db_user.save()
    return {"message":"successfully reset password"}

'''

    with open(os.path.join(main_folder, "routers", "user_routes.py"), "w", encoding='utf-8') as f:
        f.write(router_content)

    print("Auth structure created successfully!")
    print(f"Main folder: {main_folder}")
    print("Folders created: models, schemas, routers")
    print("Files created:")
    print("  - models/user_model.py")
    print("  - schemas/user_schemas.py")
    print("  - routers/user_routes.py")

# Function call
if __name__ == "__main__":
    create_auth_structure()