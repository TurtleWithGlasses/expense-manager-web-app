"""Profile management endpoints"""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from PIL import Image
import io

from app.core.session import require_session
from app.db.session import get_db
from app.models.user import User

router = APIRouter()


# Ensure uploads directory exists
UPLOAD_DIR = Path("static/uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/api/profile/update")
async def update_profile(
    full_name: str = Form(None),
    sess: dict = Depends(require_session),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    user = db.query(User).filter(User.id == sess["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update full name if provided
    if full_name is not None:
        # Validate name length
        full_name = full_name.strip()
        if len(full_name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
        if len(full_name) > 100:
            raise HTTPException(status_code=400, detail="Name must be less than 100 characters")

        user.full_name = full_name

    db.commit()
    db.refresh(user)

    return JSONResponse({
        "success": True,
        "message": "Profile updated successfully",
        "user": {
            "full_name": user.full_name,
            "email": user.email,
            "avatar_url": user.avatar_url
        }
    })


@router.post("/api/profile/avatar/upload")
async def upload_avatar(
    file: UploadFile = File(...),
    sess: dict = Depends(require_session),
    db: Session = Depends(get_db)
):
    """Upload and update user avatar"""
    user = db.query(User).filter(User.id == sess["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    contents = await file.read()

    # Validate file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    try:
        # Open image with PIL
        image = Image.open(io.BytesIO(contents))

        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background

        # Resize to square (256x256)
        size = 256
        image.thumbnail((size, size), Image.Resampling.LANCZOS)

        # Create square canvas
        square_image = Image.new('RGB', (size, size), (255, 255, 255))
        # Center the image
        offset = ((size - image.size[0]) // 2, (size - image.size[1]) // 2)
        square_image.paste(image, offset)

        # Generate filename
        filename = f"user_{user.id}.jpg"
        filepath = UPLOAD_DIR / filename

        # Delete old avatar if exists
        if user.avatar_url and user.avatar_url.startswith('/static/uploads/avatars/'):
            old_filepath = Path(user.avatar_url.lstrip('/').replace('/', os.sep))
            if old_filepath.exists():
                old_filepath.unlink()

        # Save image
        square_image.save(filepath, "JPEG", quality=90, optimize=True)

        # Update user avatar URL
        user.avatar_url = f"/static/uploads/avatars/{filename}"
        db.commit()
        db.refresh(user)

        return JSONResponse({
            "success": True,
            "message": "Avatar uploaded successfully",
            "avatar_url": user.avatar_url
        })

    except Exception as e:
        print(f"Error processing image: {e}")
        raise HTTPException(status_code=400, detail="Invalid image file")


@router.delete("/api/profile/avatar/delete")
async def delete_avatar(
    sess: dict = Depends(require_session),
    db: Session = Depends(get_db)
):
    """Delete user avatar"""
    user = db.query(User).filter(User.id == sess["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete avatar file if exists
    if user.avatar_url and user.avatar_url.startswith('/static/uploads/avatars/'):
        filepath = Path(user.avatar_url.lstrip('/').replace('/', os.sep))
        if filepath.exists():
            filepath.unlink()

    # Clear avatar URL
    user.avatar_url = None
    db.commit()
    db.refresh(user)

    return JSONResponse({
        "success": True,
        "message": "Avatar deleted successfully"
    })


@router.get("/api/profile/me")
async def get_profile(
    sess: dict = Depends(require_session),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    user = db.query(User).filter(User.id == sess["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse({
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    })
