"""
Change endpoint from PUT /info/update to PATCH /update/info

This matches what frontend expects to prevent the 404 error.

Frontend expects: PATCH /api/v1/users/update/info
Backend had: PUT /api/v1/users/info/update
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
from api_naturalize.auth.models.user_model import UserModel
from api_naturalize.utils.user_info import get_user_info

router = APIRouter(prefix="/users", tags=["users"])


# Schema for profile updates
class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = None
    fname: Optional[str] = None
    first_name: Optional[str] = None
    lname: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_image: Optional[str] = None
    password: Optional[str] = None


@router.get("/info/me", status_code=status.HTTP_200_OK)
async def get_current_user(user_data: dict = Depends(get_user_info)):
    """
    GET /api/v1/users/info/me
    
    Get complete profile of authenticated user
    Called after login to fetch full user data
    """
    try:
        user_id = user_data.get("user_id")

        user = await UserModel.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_dict = user.model_dump()

        response_data = {
            "id": user_dict.get("id"),
            "email": user_dict.get("email"),
            "username": user_dict.get("email", "").split("@")[0],
            
            # Name fields with fallbacks
            "name": f"{user_dict.get('first_name', '')} {user_dict.get('last_name', '')}".strip() or "User",
            "fname": user_dict.get("first_name") or "",
            "lname": user_dict.get("last_name") or "",
            "first_name": user_dict.get("first_name"),
            "last_name": user_dict.get("last_name"),
            
            # Profile fields
            "avatar_url": user_dict.get("profile_image") or user_dict.get("avatar_url"),
            "profile_image": user_dict.get("profile_image"),
            "phone": user_dict.get("phone_number"),
            "phone_number": user_dict.get("phone_number"),
            "bio": user_dict.get("bio"),
            "role": user_dict.get("role") or "user",
            
            # Timestamps
            "created_at": user_dict.get("created_at"),
            "updated_at": user_dict.get("updated_at"),
        }

        return {
            "data": response_data,
            "success": True,
            "message": "User profile fetched successfully"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error fetching user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {str(e)}"
        )


# Changed from PUT to PATCH and fixed path  *** _ ***
# OLD: @router.put("/info/update", ...)
# NEW: @router.patch("/update/info", ...) - matches frontend!
@router.patch("/update/info", status_code=status.HTTP_200_OK)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    user_data: dict = Depends(get_user_info)
):
    """
    PATCH /api/v1/users/update/info
    
    Update user profile (name, email, phone, bio, password, etc.)
    
    Body:
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone_number": "+1234567890",
        "bio": "My bio here",
        "password": "newpassword123",
        "profile_image": "url_to_image"
    }
    
    Response:
    {
        "success": true,
        "message": "Profile updated successfully",
        "data": { updated user object }
    }
    """
    try:
        user_id = user_data.get("user_id")
        user = await UserModel.get(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prepare update data (exclude None values)
        update_data = {}
        
        # Handle name fields (support both fname/lname and first_name/last_name)
        if profile_update.first_name is not None:
            update_data["first_name"] = profile_update.first_name
        if profile_update.fname is not None:
            update_data["first_name"] = profile_update.fname
            
        if profile_update.last_name is not None:
            update_data["last_name"] = profile_update.last_name
        if profile_update.lname is not None:
            update_data["last_name"] = profile_update.lname
            
        if profile_update.email is not None:
            update_data["email"] = profile_update.email
            
        if profile_update.phone_number is not None:
            update_data["phone_number"] = profile_update.phone_number
        if profile_update.phone is not None:
            update_data["phone_number"] = profile_update.phone
            
        if profile_update.bio is not None:
            update_data["bio"] = profile_update.bio
            
        if profile_update.profile_image is not None:
            update_data["profile_image"] = profile_update.profile_image
        if profile_update.avatar_url is not None:
            update_data["profile_image"] = profile_update.avatar_url
        
        # Handle password separately (with hashing in production)
        if profile_update.password is not None:
            from api_naturalize.utils.get_hashed_password import get_hashed_password
            update_data["password"] = get_hashed_password(profile_update.password)
            print("✅ Password updated with hashing")

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Update user in database
        await user.update({"$set": update_data})

        # Fetch updated user
        updated_user = await UserModel.get(user_id)
        user_dict = updated_user.model_dump()

        response_data = {
            "id": user_dict.get("id"),
            "email": user_dict.get("email"),
            "username": user_dict.get("email", "").split("@")[0],
            "name": f"{user_dict.get('first_name', '')} {user_dict.get('last_name', '')}".strip(),
            "first_name": user_dict.get("first_name"),
            "last_name": user_dict.get("last_name"),
            "fname": user_dict.get("first_name"),
            "lname": user_dict.get("last_name"),
            "phone_number": user_dict.get("phone_number"),
            "phone": user_dict.get("phone_number"),
            "bio": user_dict.get("bio"),
            "profile_image": user_dict.get("profile_image"),
            "avatar_url": user_dict.get("profile_image"),
        }

        return {
            "data": response_data,
            "success": True,
            "message": "Profile updated successfully"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )


@router.get("/info/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_profile(user_id: str):
    """
    GET /api/v1/users/info/{user_id}
    
    Get public user profile by ID
    """
    try:
        user = await UserModel.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_dict = user.model_dump()

        response_data = {
            "id": user_dict.get("id"),
            "username": user_dict.get("email", "").split("@")[0],
            "name": f"{user_dict.get('first_name', '')} {user_dict.get('last_name', '')}".strip(),
            "avatar_url": user_dict.get("profile_image"),
            "bio": user_dict.get("bio"),
        }

        return {
            "data": response_data,
            "success": True,
            "message": "User profile fetched successfully"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}"
        )
        
        
        #  *** _ *** #