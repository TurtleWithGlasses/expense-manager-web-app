"""Profile management endpoints"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from PIL import Image
import io

from app.deps import current_user
from app.db.session import get_db
from app.models.user import User
from app.models.entry import Entry
from app.models.category import Category
from app.models.user_preferences import UserPreferences
from app.models.weekly_report import UserReportPreferences

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
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information"""

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
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Upload and update user avatar"""

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
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Delete user avatar"""

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
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""

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


@router.get("/api/profile/export")
async def export_user_data(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Export all user data as JSON"""

    # Get all user data
    entries = db.query(Entry).filter(Entry.user_id == user.id).all()
    categories = db.query(Category).filter(Category.user_id == user.id).all()
    preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    report_prefs = db.query(UserReportPreferences).filter(UserReportPreferences.user_id == user.id).first()

    # Build export data structure
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "user": {
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_verified": user.is_verified
        },
        "preferences": {
            "currency_code": preferences.currency_code if preferences else "USD",
            "theme": preferences.theme if preferences else "dark",
            "custom_preferences": preferences.preferences if preferences else {}
        },
        "report_preferences": {
            "send_email": report_prefs.send_email if report_prefs else True,
            "show_on_dashboard": report_prefs.show_on_dashboard if report_prefs else True,
            "frequency": report_prefs.frequency if report_prefs else "weekly"
        } if report_prefs else None,
        "categories": [
            {
                "name": cat.name,
                "type": cat.type,
                "icon": cat.icon,
                "created_at": cat.created_at.isoformat() if cat.created_at else None
            }
            for cat in categories
        ],
        "entries": [
            {
                "amount": float(entry.amount),
                "description": entry.description,
                "date": entry.date.isoformat() if entry.date else None,
                "type": entry.type,
                "category_name": entry.category.name if entry.category else None,
                "notes": entry.notes,
                "created_at": entry.created_at.isoformat() if entry.created_at else None
            }
            for entry in entries
        ],
        "statistics": {
            "total_entries": len(entries),
            "total_categories": len(categories),
            "total_expenses": sum(float(e.amount) for e in entries if e.type == "expense"),
            "total_income": sum(float(e.amount) for e in entries if e.type == "income")
        }
    }

    # Convert to JSON string
    json_data = json.dumps(export_data, indent=2, ensure_ascii=False)

    # Create filename with timestamp
    filename = f"expense_manager_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(json_data.encode('utf-8')),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.delete("/api/profile/account")
async def delete_account(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Permanently delete user account and all associated data"""

    try:
        # Delete avatar file if exists
        if user.avatar_url:
            avatar_path = Path(user.avatar_url.lstrip('/'))
            if avatar_path.exists():
                avatar_path.unlink()

        # Delete user (cascade will handle related records)
        db.delete(user)
        db.commit()

        return JSONResponse({
            "success": True,
            "message": "Account deleted successfully"
        })

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")
