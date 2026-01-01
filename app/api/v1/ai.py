from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.deps import current_user
from app.db.session import get_db
from app.templates import render
from app.services.ai_service import AICategorizationService
from app.models.ai_model import UserAIPreferences
from app.ai.data.time_series_analyzer import TimeSeriesAnalyzer
from app.ai.services.prediction_service import PredictionService
from app.ai.services.anomaly_detection import AnomalyDetectionService
from app.ai.services.financial_insights import FinancialInsightsService

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

    # Get model status for template
    model_status = ai_service.get_model_status(user.id)

    return render(request, "settings/ai_settings.html", {
        "user": user,
        "preferences": preferences,
        "model_status": model_status,
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


@router.get("/analytics/weekly")
async def get_weekly_analytics(
    weeks_back: int = Query(12, ge=1, le=52),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get weekly spending analysis
    
    Args:
        weeks_back: Number of weeks to analyze (1-52, default 12)
    """
    analyzer = TimeSeriesAnalyzer(db)
    analysis = analyzer.get_weekly_analysis(user.id, weeks_back)
    
    return JSONResponse({
        "success": True,
        "data": analysis,
        "period": f"Last {weeks_back} weeks"
    })


@router.get("/analytics/monthly")
async def get_monthly_analytics(
    months_back: int = Query(12, ge=1, le=36),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get monthly spending analysis
    
    Args:
        months_back: Number of months to analyze (1-36, default 12)
    """
    analyzer = TimeSeriesAnalyzer(db)
    analysis = analyzer.get_monthly_analysis(user.id, months_back)
    
    return JSONResponse({
        "success": True,
        "data": analysis,
        "period": f"Last {months_back} months"
    })


@router.get("/analytics/annual")
async def get_annual_analytics(
    years_back: int = Query(3, ge=1, le=10),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get annual spending analysis
    
    Args:
        years_back: Number of years to analyze (1-10, default 3)
    """
    analyzer = TimeSeriesAnalyzer(db)
    analysis = analyzer.get_annual_analysis(user.id, years_back)
    
    return JSONResponse({
        "success": True,
        "data": analysis,
        "period": f"Last {years_back} years"
    })


@router.get("/analytics/patterns")
async def detect_spending_patterns(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """Detect comprehensive spending patterns across all time scales"""
    analyzer = TimeSeriesAnalyzer(db)
    patterns = analyzer.detect_spending_patterns(user.id)

    return JSONResponse({
        "success": True,
        "patterns": patterns
    })


# ============================================================================
# PHASE 15: PREDICTIVE ANALYTICS & ANOMALY DETECTION ENDPOINTS
# ============================================================================

@router.get("/predictions/next-month")
async def predict_next_month_spending(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Predict spending for the next month using time series analysis

    Returns:
        - Predicted amount
        - Confidence interval (95%)
        - Historical trend
        - Model accuracy metrics
    """
    prediction_service = PredictionService(db)
    result = prediction_service.predict_next_month_spending(user.id)

    return JSONResponse(result)


@router.get("/predictions/category/{category_id}")
async def predict_category_spending(
    category_id: int,
    days_ahead: int = Query(30, ge=7, le=90),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Predict spending for a specific category

    Args:
        category_id: Category ID to predict
        days_ahead: Number of days to forecast (7-90, default 30)
    """
    prediction_service = PredictionService(db)
    result = prediction_service.predict_category_spending(user.id, category_id, days_ahead)

    return JSONResponse(result)


@router.get("/predictions/cash-flow")
async def predict_cash_flow(
    months_ahead: int = Query(3, ge=1, le=12),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Predict cash flow (income - expenses) for upcoming months

    Args:
        months_ahead: Number of months to forecast (1-12, default 3)
    """
    prediction_service = PredictionService(db)
    result = prediction_service.predict_cash_flow(user.id, months_ahead)

    return JSONResponse(result)


@router.get("/predictions/budget-status")
async def predict_budget_status(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Predict if user will stay within budget for current month

    Returns:
        - Current spending status
        - Predicted end-of-month total
        - Comparison with previous month
        - Personalized recommendations
    """
    prediction_service = PredictionService(db)
    result = prediction_service.predict_budget_status(user.id)

    return JSONResponse(result)


@router.get("/predictions/forecast-data")
async def get_forecast_data(
    months_back: int = Query(6, ge=3, le=24),
    months_ahead: int = Query(3, ge=1, le=12),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive forecast data for visualization

    Args:
        months_back: Historical months to include (3-24, default 6)
        months_ahead: Future months to forecast (1-12, default 3)

    Returns:
        Historical data + predictions with confidence intervals for charts
    """
    prediction_service = PredictionService(db)
    result = prediction_service.get_spending_forecast_data(user.id, months_back, months_ahead)

    return JSONResponse(result)


@router.get("/anomalies/detect")
async def detect_spending_anomalies(
    days_back: int = Query(90, ge=30, le=365),
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Detect unusual spending patterns using machine learning

    Args:
        days_back: Number of days to analyze (30-365, default 90)

    Returns:
        - List of anomalous transactions
        - Severity levels (low/medium/high)
        - Explanations for each anomaly
        - Summary statistics
    """
    anomaly_service = AnomalyDetectionService(db)
    result = anomaly_service.detect_spending_anomalies(user.id, days_back)

    return JSONResponse(result)


@router.get("/anomalies/category/{category_id}")
async def detect_category_anomalies(
    category_id: int,
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Detect anomalies within a specific category

    Args:
        category_id: Category ID to analyze

    Returns:
        Category-specific anomalies with statistical analysis
    """
    anomaly_service = AnomalyDetectionService(db)
    result = anomaly_service.detect_category_anomalies(user.id, category_id)

    return JSONResponse(result)


@router.get("/anomalies/recurring")
async def detect_recurring_anomalies(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Detect recurring transactions with unusual amounts

    Identifies subscriptions or bills that have changed unexpectedly
    """
    anomaly_service = AnomalyDetectionService(db)
    result = anomaly_service.detect_recurring_anomalies(user.id)

    return JSONResponse(result)


@router.get("/anomalies/insights")
async def get_anomaly_insights(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive anomaly insights and recommendations

    Returns:
        - Key insights about unusual spending
        - Actionable recommendations
        - Detailed anomaly breakdowns
    """
    anomaly_service = AnomalyDetectionService(db)
    result = anomaly_service.get_anomaly_insights(user.id)

    return JSONResponse(result)


# ============================================================================
# PHASE 16: SMART FINANCIAL INSIGHTS & RECOMMENDATIONS
# ============================================================================

@router.get("/insights/comprehensive")
async def get_comprehensive_insights(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive financial insights and recommendations

    Returns:
        - Spending pattern analysis
        - Saving opportunities
        - Budget health assessment
        - Category trends
        - Personalized recommendations
        - Achievements
        - Alerts
    """
    insights_service = FinancialInsightsService(db)
    result = insights_service.get_comprehensive_insights(user.id)

    return JSONResponse(result)


@router.get("/insights/spending-patterns")
async def get_spending_patterns(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze user's spending patterns and habits

    Returns:
        - Most active spending day
        - Highest spending day
        - Average transaction amount
        - Spending consistency
        - Monthly spending phase pattern
    """
    insights_service = FinancialInsightsService(db)
    patterns = insights_service._analyze_spending_patterns(user.id)

    return JSONResponse({
        'success': True,
        'patterns': patterns
    })


@router.get("/insights/saving-opportunities")
async def get_saving_opportunities(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Identify opportunities to save money

    Returns:
        - High-volume categories with savings potential
        - Frequent small purchase patterns
        - Potential monthly savings
        - Prioritized recommendations
    """
    insights_service = FinancialInsightsService(db)
    opportunities = insights_service._identify_saving_opportunities(user.id)

    return JSONResponse({
        'success': True,
        'opportunities': opportunities,
        'total_opportunities': len(opportunities)
    })


@router.get("/insights/budget-health")
async def get_budget_health(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Assess overall budget health

    Returns:
        - Health score (0-100)
        - Status (excellent/good/fair/poor)
        - Current and previous savings rate
        - Expense change percentage
        - Status message with recommendations
    """
    insights_service = FinancialInsightsService(db)
    health = insights_service._assess_budget_health(user.id)

    return JSONResponse({
        'success': True,
        'budget_health': health
    })


@router.get("/insights/category-trends")
async def get_category_trends(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze spending trends by category over last 6 months

    Returns:
        - Category-wise trend analysis
        - Trend direction (increasing/decreasing/stable)
        - Trend percentage
        - Average monthly spending per category
    """
    insights_service = FinancialInsightsService(db)
    trends = insights_service._analyze_category_trends(user.id)

    return JSONResponse({
        'success': True,
        'trends': trends,
        'total_categories': len(trends)
    })


@router.get("/insights/recommendations")
async def get_recommendations(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized financial recommendations

    Returns:
        - Prioritized recommendations
        - Action items
        - Potential impact assessment
        - Implementation suggestions
    """
    insights_service = FinancialInsightsService(db)
    recommendations = insights_service._generate_recommendations(user.id)

    return JSONResponse({
        'success': True,
        'recommendations': recommendations,
        'total_recommendations': len(recommendations)
    })


@router.get("/insights/achievements")
async def get_achievements(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get financial achievements and milestones

    Returns:
        - Positive achievements
        - Milestone celebrations
        - Progress indicators
    """
    insights_service = FinancialInsightsService(db)
    achievements = insights_service._identify_achievements(user.id)

    return JSONResponse({
        'success': True,
        'achievements': achievements,
        'total_achievements': len(achievements)
    })


@router.get("/insights/alerts")
async def get_financial_alerts(
    user=Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get important financial alerts

    Returns:
        - Budget health warnings
        - Spending alerts
        - Actionable notifications
        - Severity-based prioritization
    """
    insights_service = FinancialInsightsService(db)
    alerts = insights_service._generate_alerts(user.id)

    return JSONResponse({
        'success': True,
        'alerts': alerts,
        'total_alerts': len(alerts)
    })
