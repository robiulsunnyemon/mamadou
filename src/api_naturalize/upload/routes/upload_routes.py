"""
File Upload Routes
Handles image uploads with validation and returns proper URL
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pathlib import Path
import uuid
import os
from typing import Optional

router = APIRouter(prefix="/upload", tags=["upload"])

# Configuration
UPLOAD_DIR = Path("static")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_file_size(file_bytes: bytes) -> int:
    """Get file size in bytes"""
    return len(file_bytes)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a single file and return the file URL
    
    Request:
        - file: UploadFile (multipart/form-data)
    
    Response:
        {
            "success": true,
            "message": "File uploaded successfully",
            "data": {
                "url": "http://localhost:8000/static/filename.jpg",
                "filename": "uuid.jpg",
                "original_filename": "profile.jpg"
            }
        }
    
    Errors:
        - 400: Invalid file type
        - 413: File too large
        - 500: Upload failed
    """
    try:
        # Validate file extension
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Read file contents
        contents = await file.read()

        # Validate file size
        file_size = get_file_size(contents)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)

        # Get the base URL from environment or default
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        file_url = f"{base_url}/static/{unique_filename}"

        return {
            "success": True,
            "message": "File uploaded successfully",
            "data": {
                "url": file_url,
                "filename": unique_filename,
                "original_filename": file.filename,
                "size": file_size
            }
        }

    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e

    except Exception as e:
        # Log the error for debugging
        print(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.post("/multiple", status_code=status.HTTP_201_CREATED)
async def upload_multiple_files(files: list[UploadFile] = File(...)):
    """
    Upload multiple files at once
    
    Request:
        - files: List[UploadFile] (multipart/form-data)
    
    Response:
        {
            "success": true,
            "message": "2 files uploaded successfully",
            "data": [
                {
                    "url": "...",
                    "filename": "...",
                    "original_filename": "..."
                }
            ],
            "failed": []
        }
    """
    try:
        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                if not allowed_file(file.filename):
                    failed_files.append({
                        "filename": file.filename,
                        "error": f"File type not allowed"
                    })
                    continue

                contents = await file.read()
                file_size = get_file_size(contents)

                if file_size > MAX_FILE_SIZE:
                    failed_files.append({
                        "filename": file.filename,
                        "error": f"File too large (max {MAX_FILE_SIZE / 1024 / 1024}MB)"
                    })
                    continue

                if file_size == 0:
                    failed_files.append({
                        "filename": file.filename,
                        "error": "File is empty"
                    })
                    continue

                # Generate unique filename
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{file_extension}"
                file_path = UPLOAD_DIR / unique_filename

                # Save file
                with open(file_path, "wb") as f:
                    f.write(contents)

                # Build URL
                base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
                file_url = f"{base_url}/static/{unique_filename}"

                uploaded_files.append({
                    "url": file_url,
                    "filename": unique_filename,
                    "original_filename": file.filename,
                    "size": file_size
                })

            except Exception as e:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })

        return {
            "success": len(uploaded_files) > 0,
            "message": f"{len(uploaded_files)} file(s) uploaded successfully",
            "data": uploaded_files,
            "failed": failed_files
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch upload failed: {str(e)}"
        )   
        
        
        #  *** _ ***