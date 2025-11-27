"""
User Feedback API Endpoints

Allows users to submit feedback and admins to manage it.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.deps import current_user, admin_user
from app.models.user import User
from app.services.feedback_service import get_feedback_service
from app.templates import render

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.get("/", response_class=HTMLResponse)
def feedback_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Feedback submission page for users

    Allows users to:
    - Submit bug reports
    - Request features
    - Provide general feedback
    - Rate the application
    """
    feedback_service = get_feedback_service(db)

    # Get user's previous feedback
    user_feedback = feedback_service.get_user_feedback(user.id)

    return render(
        request,
        "feedback/index.html",
        {
            "user": user,
            "user_feedback": user_feedback,
        }
    )


@router.post("/submit")
async def submit_feedback(
    feedback_type: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    rating: Optional[int] = Form(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Submit new feedback

    Form fields:
    - feedback_type: 'bug', 'feature', or 'feedback'
    - subject: Short summary
    - message: Detailed message
    - rating: Optional 1-5 star rating
    """
    # Validate feedback type
    if feedback_type not in ['bug', 'feature', 'feedback']:
        raise HTTPException(status_code=400, detail="Invalid feedback type")

    # Validate rating if provided
    if rating is not None and (rating < 1 or rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    feedback_service = get_feedback_service(db)

    # Submit feedback
    feedback = feedback_service.submit_feedback(
        user_id=user.id,
        feedback_type=feedback_type,
        subject=subject,
        message=message,
        rating=rating
    )

    return RedirectResponse(
        url="/feedback?success=true",
        status_code=303
    )


@router.get("/admin", response_class=HTMLResponse)
def admin_feedback_page(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    feedback_type: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin feedback management page

    Shows:
    - All feedback submissions
    - Filter by type and status
    - Respond to feedback
    - Mark as resolved
    """
    feedback_service = get_feedback_service(db)

    # Get feedback list
    result = feedback_service.get_all_feedback(
        page=page,
        per_page=per_page,
        feedback_type=feedback_type,
        is_resolved=is_resolved
    )

    # Get statistics
    stats = feedback_service.get_feedback_statistics()

    return render(
        request,
        "admin/feedback.html",
        {
            "user": admin,
            "feedback_list": result["feedback"],
            "pagination": result["pagination"],
            "stats": stats,
            "filter_type": feedback_type,
            "filter_resolved": is_resolved,
        }
    )


@router.post("/admin/{feedback_id}/respond")
async def admin_respond_feedback(
    feedback_id: int,
    admin_response: str = Form(...),
    mark_resolved: bool = Form(True),
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin responds to feedback

    Form fields:
    - admin_response: Response message
    - mark_resolved: Whether to mark as resolved
    """
    feedback_service = get_feedback_service(db)

    feedback = feedback_service.respond_to_feedback(
        feedback_id=feedback_id,
        admin_response=admin_response,
        mark_resolved=mark_resolved
    )

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return RedirectResponse(
        url="/feedback/admin",
        status_code=303
    )


@router.get("/api/statistics")
def feedback_statistics_api(
    admin: User = Depends(admin_user),
    db: Session = Depends(get_db)
):
    """API endpoint for feedback statistics"""
    feedback_service = get_feedback_service(db)
    stats = feedback_service.get_feedback_statistics()

    return JSONResponse(content=stats)
