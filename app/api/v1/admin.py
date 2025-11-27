"""
Admin API Endpoints

Provides administrative functionality for:
- User management
- System monitoring
- Statistics dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.deps import admin_user
from app.models.user import User
from app.services.admin_service import get_admin_service
from app.templates import render

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin dashboard page

    Shows:
    - User statistics
    - System health metrics
    - Recent activity
    - Quick actions
    """
    admin_service = get_admin_service(db)

    # Get dashboard statistics
    stats = admin_service.get_dashboard_statistics()

    # Get system health
    health = admin_service.get_system_health_metrics()

    # Get recent user activity (last 30 days)
    activity = admin_service.get_user_activity_stats(days=30)

    return render(
        request,
        "admin/dashboard.html",
        {
            "user": admin,
            "stats": stats,
            "health": health,
            "activity": activity,
        }
    )


@router.get("/users", response_class=HTMLResponse)
def admin_users_page(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    filter_verified: Optional[bool] = None,
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """
    User management page

    Shows:
    - Paginated list of all users
    - Search by email or name
    - Filter by verification status
    - User actions (view, delete, reset password)
    """
    admin_service = get_admin_service(db)

    # Get user list
    result = admin_service.get_user_list(
        page=page,
        per_page=per_page,
        search=search,
        filter_verified=filter_verified
    )

    return render(
        request,
        "admin/users.html",
        {
            "user": admin,
            "users": result["users"],
            "pagination": result["pagination"],
            "search": search or "",
            "filter_verified": filter_verified,
        }
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
def admin_user_details(
    request: Request,
    user_id: int,
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """
    User details page

    Shows:
    - Complete user information
    - Activity statistics
    - Account history
    - Admin actions
    """
    admin_service = get_admin_service(db)

    # Get user details
    user_details = admin_service.get_user_details(user_id)
    if not user_details:
        raise HTTPException(status_code=404, detail="User not found")

    return render(
        request,
        "admin/user_details.html",
        {
            "user": admin,
            "target_user": user_details,
        }
    )


@router.get("/system-health", response_class=JSONResponse)
def system_health_api(
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """API endpoint for system health metrics"""
    admin_service = get_admin_service(db)
    health = admin_service.get_system_health_metrics()

    return JSONResponse(content=health)


@router.get("/statistics", response_class=JSONResponse)
def dashboard_statistics_api(
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """API endpoint for dashboard statistics"""
    admin_service = get_admin_service(db)
    stats = admin_service.get_dashboard_statistics()

    return JSONResponse(content=stats)


@router.post("/users/{user_id}/delete")
def delete_user_account_admin(
    user_id: int,
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete user account (admin action)

    Cascading deletes will handle all related data
    Cannot delete admin users
    """
    admin_service = get_admin_service(db)

    success = admin_service.delete_user_account(user_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete user (user not found or is admin)"
        )

    return JSONResponse(content={
        "success": True,
        "message": "User account deleted successfully"
    })


@router.post("/users/{user_id}/resend-verification")
def resend_verification_admin(
    user_id: int,
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """Admin-initiated verification email resend"""
    admin_service = get_admin_service(db)

    success = admin_service.resend_verification_email(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse(content={
        "success": True,
        "message": "Verification email sent"
    })
