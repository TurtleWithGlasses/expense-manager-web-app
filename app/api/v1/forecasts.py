"""
API endpoints for Prophet-based forecasting

Phase 4: Advanced ML Features - Prophet Integration
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.models.forecast import Forecast
from app.models.user_preferences import UserPreferences
from app.ai.services.prophet_forecast_service import ProphetForecastService
from app.core.currency import get_currency_info

router = APIRouter(prefix="/api/v1/forecasts", tags=["Forecasts"])


@router.get("/spending/total")
def forecast_total_spending(
    days_ahead: int = Query(90, ge=7, le=365, description="Days to forecast (7-365)"),
    include_history: bool = Query(True, description="Include historical data"),
    use_cache: bool = Query(True, description="Use cached forecast if available"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Forecast total spending using Facebook Prophet

    **Features:**
    - Seasonal pattern detection (weekly, monthly, yearly)
    - Trend analysis
    - 95% confidence intervals
    - Automatic holiday detection
    - Multi-horizon forecasting

    **Returns:**
    - Forecast data with confidence bands
    - Historical data for comparison
    - Insights and recommendations
    - Model diagnostics
    """
    try:
        # Get user's currency preference
        user_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        currency_code = user_prefs.currency_code if user_prefs else 'USD'
        currency_info = get_currency_info(currency_code)

        # Check for cached forecast (less than 24 hours old)
        if use_cache:
            cached_forecast = db.query(Forecast).filter(
                Forecast.user_id == user.id,
                Forecast.forecast_type == 'total_spending',
                Forecast.forecast_horizon_days == days_ahead,
                Forecast.is_active == True,
                Forecast.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).order_by(Forecast.created_at.desc()).first()

            if cached_forecast:
                return {
                    'success': True,
                    'cached': True,
                    'forecast': cached_forecast.forecast_data,
                    'historical': cached_forecast.summary.get('historical', []) if cached_forecast.summary else [],
                    'summary': cached_forecast.summary,
                    'insights': cached_forecast.insights,
                    'created_at': cached_forecast.created_at.isoformat(),
                    'currency': {
                        'code': currency_code,
                        'symbol': currency_info['symbol'],
                        'name': currency_info['name']
                    }
                }

        # Generate new forecast
        service = ProphetForecastService(db)
        result = service.forecast_total_spending(
            user_id=user.id,
            days_ahead=days_ahead,
            include_history=include_history
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', 'Forecasting failed'))

        # Save forecast to database
        forecast = Forecast(
            user_id=user.id,
            forecast_type='total_spending',
            forecast_horizon_days=days_ahead,
            training_data_start=datetime.now() - timedelta(days=180),
            training_data_end=datetime.now(),
            training_data_points=result['model_info']['training_days'],
            forecast_data=result['forecast'],
            summary=result['summary'],
            insights=result['insights'],
            model_type='prophet',
            confidence_level=0.95,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_active=True
        )

        db.add(forecast)
        db.commit()

        return {
            **result,
            'cached': False,
            'forecast_id': forecast.id,
            'currency': {
                'code': currency_code,
                'symbol': currency_info['symbol'],
                'name': currency_info['name']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")


@router.get("/spending/category/{category_id}")
def forecast_category_spending(
    category_id: int,
    months_ahead: int = Query(3, ge=1, le=12, description="Months to forecast (1-12)"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Forecast spending for a specific category

    **Use Cases:**
    - Predict monthly grocery spending
    - Forecast utility bills
    - Estimate transportation costs
    - Plan category budgets

    **Returns:**
    - Monthly forecast totals
    - Confidence intervals
    - Historical comparison
    """
    try:
        service = ProphetForecastService(db)
        result = service.forecast_by_category(
            user_id=user.id,
            category_id=category_id,
            months_ahead=months_ahead
        )

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', 'Category forecasting failed'))

        # Save forecast
        forecast = Forecast(
            user_id=user.id,
            forecast_type='category',
            category_id=category_id,
            forecast_horizon_days=months_ahead * 30,
            training_data_start=datetime.now() - timedelta(days=180),
            training_data_end=datetime.now(),
            training_data_points=result.get('weeks_analyzed', 0),
            forecast_data=result['monthly_forecasts'],
            summary={'historical_monthly_avg': result.get('historical_monthly_avg')},
            model_type='prophet',
            confidence_level=0.80,
            expires_at=datetime.utcnow() + timedelta(hours=48),
            is_active=True
        )

        db.add(forecast)
        db.commit()

        return {
            **result,
            'forecast_id': forecast.id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Category forecasting error: {str(e)}")


@router.get("/patterns/seasonal")
def detect_seasonal_patterns(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Detect and analyze seasonal spending patterns

    **Detects:**
    - Weekly patterns (e.g., weekend spending)
    - Monthly patterns (e.g., payday cycles)
    - Yearly patterns (e.g., holiday shopping)

    **Returns:**
    - Pattern strength (strong/moderate/weak)
    - Seasonal insights
    - Recommendations
    """
    try:
        service = ProphetForecastService(db)
        result = service.detect_seasonal_patterns(user_id=user.id)

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', 'Seasonal analysis failed'))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seasonal analysis error: {str(e)}")


@router.get("/history")
def get_forecast_history(
    forecast_type: str = Query(None, description="Filter by forecast type"),
    limit: int = Query(10, ge=1, le=50, description="Number of forecasts to return"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's forecast history

    **Use Cases:**
    - Review past predictions
    - Track forecast accuracy
    - Compare forecasts over time
    """
    query = db.query(Forecast).filter(
        Forecast.user_id == user.id,
        Forecast.is_active == True
    )

    if forecast_type:
        query = query.filter(Forecast.forecast_type == forecast_type)

    forecasts = query.order_by(Forecast.created_at.desc()).limit(limit).all()

    return {
        'success': True,
        'forecasts': [f.to_dict() for f in forecasts],
        'total_count': len(forecasts)
    }


@router.get("/accuracy/{forecast_id}")
def get_forecast_accuracy(
    forecast_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Get accuracy metrics for a past forecast

    **Metrics:**
    - MAPE (Mean Absolute Percentage Error)
    - Actual vs Predicted comparison
    - Confidence interval performance

    **Note:** Only available for forecasts where actual data is now available
    """
    forecast = db.query(Forecast).filter(
        Forecast.id == forecast_id,
        Forecast.user_id == user.id
    ).first()

    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    # TODO: Implement accuracy calculation by comparing forecast to actual data
    # This requires fetching actual spending data for the forecasted period

    return {
        'success': True,
        'forecast_id': forecast_id,
        'message': 'Accuracy calculation coming soon',
        'forecast': forecast.to_dict()
    }


@router.delete("/clear-cache")
def clear_forecast_cache(
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """
    Clear all cached forecasts for the user

    **Use Cases:**
    - Force regeneration of forecasts
    - After major spending pattern changes
    - After adding significant historical data
    """
    deleted_count = db.query(Forecast).filter(
        Forecast.user_id == user.id,
        Forecast.is_active == True
    ).update({'is_active': False})

    db.commit()

    return {
        'success': True,
        'message': f'Cleared {deleted_count} cached forecasts',
        'forecasts_cleared': deleted_count
    }
