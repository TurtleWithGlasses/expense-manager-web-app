"""Profile management endpoints"""
import os
import json
import shutil
import base64
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
from app.models.report_status import ReportStatus
from app.core.security import hash_password, verify_password
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

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

        # Resize to square (128x128) - smaller size for database storage
        size = 128
        image.thumbnail((size, size), Image.Resampling.LANCZOS)

        # Create square canvas
        square_image = Image.new('RGB', (size, size), (255, 255, 255))
        # Center the image
        offset = ((size - image.size[0]) // 2, (size - image.size[1]) // 2)
        square_image.paste(image, offset)

        # Convert image to base64 data URI
        buffered = io.BytesIO()
        square_image.save(buffered, format="JPEG", quality=85, optimize=True)
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{img_base64}"

        # Update user avatar URL with base64 data URI
        user.avatar_url = data_uri
        db.commit()
        db.refresh(user)

        return JSONResponse({
            "success": True,
            "message": "Avatar uploaded successfully",
            "avatar_url": user.avatar_url
        })

    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid image file")


@router.delete("/api/profile/avatar/delete")
async def delete_avatar(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Delete user avatar"""

    # Clear avatar URL (no need to delete files since we store in database now)
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
                "id": cat.id,
                "name": cat.name
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
                "note": entry.note,
                "currency_code": entry.currency_code
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
    json_bytes = json_data.encode('utf-8')

    # Create filename with timestamp
    filename = f"expense_manager_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    # Return as downloadable file
    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(json_bytes))
        }
    )


@router.put("/api/profile/password")
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""

    try:
        logger.info(f"Password change attempt for user: {user.email}")

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            logger.warning(f"Failed password change for {user.email}: incorrect current password")
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Validate new password length
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

        # Check password strength requirements
        has_uppercase = any(c.isupper() for c in new_password)
        has_lowercase = any(c.islower() for c in new_password)
        has_number = any(c.isdigit() for c in new_password)

        if not (has_uppercase and has_lowercase and has_number):
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least one uppercase letter, one lowercase letter, and one number"
            )

        # Check if new password is same as current
        if verify_password(new_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="New password must be different from current password")

        # Hash and update password
        user.hashed_password = hash_password(new_password)
        db.commit()

        logger.info(f"Password changed successfully for user: {user.email}")

        return JSONResponse({
            "success": True,
            "message": "Password changed successfully"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password for {user.email}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to change password")


@router.delete("/api/profile/account")
async def delete_account(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Permanently delete user account and all associated data"""

    try:
        logger.info(f"Attempting to delete account for user: {user.email} (ID: {user.id})")

        user_id = user.id
        
        # Manually delete report_status records first to avoid foreign key constraint issues
        # This is a defensive measure in case the database constraint doesn't have CASCADE
        try:
            deleted_count = db.query(ReportStatus).filter(ReportStatus.user_id == user_id).delete(synchronize_session=False)
            logger.info(f"Deleted {deleted_count} report_status records for user {user_id}")
            db.flush()  # Flush to ensure the delete is executed before user deletion
        except Exception as e:
            logger.warning(f"Warning: Error deleting report_status records: {e}")
            # Continue with user deletion anyway - cascade should handle it if DB constraint is correct

        # Delete user (cascade will handle other related records)
        # No need to delete avatar files since we store in database now
        db.delete(user)
        db.commit()

        logger.info(f"Account successfully deleted for user: {user.email}")

        return JSONResponse({
            "success": True,
            "message": "Account deleted successfully"
        })

    except Exception as e:
        logger.error(f"Error deleting account: {type(e).__name__}: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")
