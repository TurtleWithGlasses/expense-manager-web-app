from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.deps import current_user
from app.db.session import get_db
from app.templates import render
from app.services.ai_service import AICategorizationService
from app.models.ai_model import UserAIPreferences

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/settings", response_class=HTMLResponse)
async def ai_settings_page(request: Request, user=Depends(current_user), db: Session = Depends(get_db)):
    """AI settings page"""
    ai_service = AICategorizationService(db)
    preferences = ai_service.get_user_ai_preferences(user.id)
    model_status = ai_service.get_model_status(user.id)
    
    return render(request, "settings/ai_settings.html", {
        "user": user,
        "preferences": preferences,
        "model_status": model_status
    })


@router.post("/settings", response_class=HTMLResponse)
async def update_ai_settings(
    request: Request,
    user=Depends(current_user),
    db: Session = Depends(get_db),
    auto_categorization_enabled: bool = Form(False),
    smart_suggestions_enabled: bool = Form(False),
    spending_insights_enabled: bool = Form(False),
    budget_predictions_enabled: bool = Form(False),
    min_confidence_threshold: float = Form(0.7),
    auto_accept_threshold: float = Form(0.9),
    learn_from_feedback: bool = Form(False),
    retrain_frequency_days: int = Form(7),
    share_anonymized_data: bool = Form(False)
):
    """Update AI settings"""
    ai_service = AICategorizationService(db)
    preferences = ai_service.get_user_ai_preferences(user.id)
    
    # Update preferences
    preferences.auto_categorization_enabled = auto_categorization_enabled
    preferences.smart_suggestions_enabled = smart_suggestions_enabled
    preferences.spending_insights_enabled = spending_insights_enabled
    preferences.budget_predictions_enabled = budget_predictions_enabled
    preferences.min_confidence_threshold = min_confidence_threshold
    preferences.auto_accept_threshold = auto_accept_threshold
    preferences.learn_from_feedback = learn_from_feedback
    preferences.retrain_frequency_days = retrain_frequency_days
    preferences.share_anonymized_data = share_anonymized_data
    
    db.commit()
    
    return render(request, "settings/ai_settings.html", {
        "user": user,
        "preferences": preferences,
        "message": "AI settings updated successfully!"
    })


@router.post("/suggest-category")
async def suggest_category(
    user=Depends(current_user),
    db: Session = Depends(get_db),
    note: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    amount: Optional[float] = Form(None),
    entry_type: Optional[str] = Form(None)
):
    """Get AI category suggestion for a new entry"""
    ai_service = AICategorizationService(db)
    
    entry_data = {
        "note": note,
        "description": description,
        "amount": amount,
        "type": entry_type
    }
    
    suggested_category_id, confidence_score = ai_service.suggest_category(user.id, entry_data)
    
    if suggested_category_id:
        # Get category name
        from app.models.category import Category
        category = db.query(Category).filter(Category.id == suggested_category_id).first()
        
        return JSONResponse({
            "success": True,
            "suggestion": {
                "category_id": suggested_category_id,
                "category_name": category.name if category else "Unknown",
                "confidence_score": round(confidence_score, 2)
            }
        })
    else:
        return JSONResponse({
            "success": False,
            "message": "No confident suggestions available"
        })


@router.post("/feedback")
async def provide_feedback(
    user=Depends(current_user),
    db: Session = Depends(get_db),
    suggestion_id: int = Form(...),
    is_accepted: bool = Form(...)
):
    """Provide feedback on AI suggestions"""
    ai_service = AICategorizationService(db)
    
    success = ai_service.record_feedback(suggestion_id, is_accepted)
    
    if success:
        return JSONResponse({
            "success": True,
            "message": "Feedback recorded successfully"
        })
    else:
        return JSONResponse({
            "success": False,
            "message": "Failed to record feedback"
        })


@router.get("/insights")
async def get_smart_insights(user=Depends(current_user), db: Session = Depends(get_db)):
    """Get smart insights for the user"""
    ai_service = AICategorizationService(db)
    insights = ai_service.get_smart_insights(user.id)
    
    return JSONResponse({
        "success": True,
        "insights": insights
    })


@router.get("/dashboard-widget", response_class=HTMLResponse)
async def ai_dashboard_widget(
    request: Request,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """AI dashboard widget with insights"""
    ai_service = AICategorizationService(db)
    insights = ai_service.get_smart_insights(user.id)
    
    return render(request, "dashboard/_ai_insights.html", {
        "user": user,
        "insights": insights
    })


@router.get("/model/status")
async def get_model_status(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get ML model training status"""
    ai_service = AICategorizationService(db)
    status = ai_service.get_model_status(user.id)
    
    return JSONResponse({
        "success": True,
        "status": status
    })


@router.post("/model/train")
async def train_model(
    background_tasks: BackgroundTasks,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Train ML model for user's transaction categorization
    
    This endpoint triggers model training in the background.
    Training requires at least 50 categorized entries.
    """
    ai_service = AICategorizationService(db)
    
    # Get current status
    status = ai_service.get_model_status(user.id)
    
    if not status['can_train']:
        return JSONResponse({
            "success": False,
            "message": f"Need at least 50 categorized entries. You have {status['training_stats']['total_categorized']}.",
            "status": status
        }, status_code=400)
    
    # Train the model (synchronously for now, can be made async later)
    result = ai_service.train_user_model(user.id)
    
    return JSONResponse(result)


@router.post("/model/retrain")
async def retrain_model(
    background_tasks: BackgroundTasks,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Retrain the ML model with latest data"""
    ai_service = AICategorizationService(db)
    
    # Train the model
    result = ai_service.train_user_model(user.id)
    
    return JSONResponse(result)
