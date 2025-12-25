"""
ScenarioService for What-If Analysis and Financial Planning

Enables users to test different financial scenarios and make data-driven decisions.
Integrates with Prophet forecasts for accurate projections.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.models.scenario import Scenario, ScenarioComparison
from app.models.entry import Entry
from app.models.category import Category
from app.models.user import User
from app.ai.services.prophet_forecast_service import ProphetForecastService
import logging

logger = logging.getLogger(__name__)


class ScenarioService:
    """
    Service for creating and analyzing financial scenarios
    """

    def __init__(self, db: Session):
        self.db = db
        self.prophet_service = ProphetForecastService(db)

    def create_scenario(
        self,
        user_id: int,
        name: str,
        scenario_type: str,
        parameters: Dict[str, Any],
        description: Optional[str] = None
    ) -> Dict:
        """
        Create a new financial scenario and calculate projected outcomes

        Args:
            user_id: User ID
            name: Scenario name (e.g., "Reduce dining by 30%")
            scenario_type: Type of scenario ('spending_reduction', 'income_increase', 'goal_based', 'category_adjustment')
            parameters: Scenario-specific parameters (JSON)
            description: Optional description

        Returns:
            Dict with scenario details and projected outcome
        """
        try:
            # Validate scenario type
            valid_types = ['spending_reduction', 'income_increase', 'goal_based', 'category_adjustment']
            if scenario_type not in valid_types:
                return {
                    'success': False,
                    'error': f'Invalid scenario type. Must be one of: {", ".join(valid_types)}'
                }

            # Validate parameters
            validation_result = self._validate_parameters(scenario_type, parameters)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error']
                }

            # Get baseline data (current financial state)
            baseline_data = self._get_baseline_data(user_id)

            # Calculate projected outcome based on scenario type
            if scenario_type == 'spending_reduction':
                projected_outcome = self._calculate_spending_reduction_outcome(user_id, parameters, baseline_data)
            elif scenario_type == 'income_increase':
                projected_outcome = self._calculate_income_increase_outcome(user_id, parameters, baseline_data)
            elif scenario_type == 'goal_based':
                projected_outcome = self._calculate_goal_based_outcome(user_id, parameters, baseline_data)
            elif scenario_type == 'category_adjustment':
                projected_outcome = self._calculate_category_adjustment_outcome(user_id, parameters, baseline_data)
            else:
                return {'success': False, 'error': 'Unsupported scenario type'}

            # Create scenario in database
            scenario = Scenario(
                user_id=user_id,
                name=name,
                description=description,
                scenario_type=scenario_type,
                parameters=parameters,
                projected_outcome=projected_outcome,
                baseline_data=baseline_data,
                is_active=True,
                is_favorite=False
            )

            self.db.add(scenario)
            self.db.commit()
            self.db.refresh(scenario)

            logger.info(f"Created scenario {scenario.id} for user {user_id}: {name}")

            return {
                'success': True,
                'scenario': scenario.to_dict(),
                'message': 'Scenario created successfully'
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating scenario: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to create scenario: {str(e)}'
            }

    def _validate_parameters(self, scenario_type: str, parameters: Dict) -> Dict:
        """Validate scenario parameters based on type"""
        try:
            if scenario_type == 'spending_reduction':
                required = ['category_id', 'reduction_percent']
                if not all(k in parameters for k in required):
                    return {'valid': False, 'error': f'Missing required parameters: {required}'}
                if not 0 < parameters['reduction_percent'] <= 100:
                    return {'valid': False, 'error': 'reduction_percent must be between 1 and 100'}

            elif scenario_type == 'income_increase':
                required = ['amount', 'frequency']
                if not all(k in parameters for k in required):
                    return {'valid': False, 'error': f'Missing required parameters: {required}'}
                if parameters['amount'] <= 0:
                    return {'valid': False, 'error': 'amount must be positive'}
                if parameters['frequency'] not in ['monthly', 'biweekly', 'weekly', 'one_time']:
                    return {'valid': False, 'error': 'Invalid frequency'}

            elif scenario_type == 'goal_based':
                required = ['target_amount', 'timeframe_months']
                if not all(k in parameters for k in required):
                    return {'valid': False, 'error': f'Missing required parameters: {required}'}
                if parameters['target_amount'] <= 0:
                    return {'valid': False, 'error': 'target_amount must be positive'}
                if parameters['timeframe_months'] < 1:
                    return {'valid': False, 'error': 'timeframe_months must be at least 1'}

            elif scenario_type == 'category_adjustment':
                if 'adjustments' not in parameters or not isinstance(parameters['adjustments'], list):
                    return {'valid': False, 'error': 'adjustments must be a list'}

            return {'valid': True}

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def _get_baseline_data(self, user_id: int) -> Dict:
        """
        Get current financial baseline for comparison

        Returns monthly averages and current state
        """
        try:
            # Get last 90 days of data
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)

            # Calculate average monthly income
            income_entries = self.db.query(func.sum(Entry.amount)).filter(
                and_(
                    Entry.user_id == user_id,
                    Entry.type == 'income',
                    Entry.date >= ninety_days_ago
                )
            ).scalar() or 0

            # Calculate average monthly expenses
            expense_entries = self.db.query(func.sum(Entry.amount)).filter(
                and_(
                    Entry.user_id == user_id,
                    Entry.type == 'expense',
                    Entry.date >= ninety_days_ago
                )
            ).scalar() or 0

            # Monthly averages (90 days = ~3 months)
            avg_monthly_income = income_entries / 3
            avg_monthly_expenses = expense_entries / 3
            avg_monthly_savings = avg_monthly_income - avg_monthly_expenses

            # Category breakdown
            category_spending = {}
            category_results = self.db.query(
                Entry.category_id,
                Category.name,
                func.sum(Entry.amount).label('total')
            ).join(Category).filter(
                and_(
                    Entry.user_id == user_id,
                    Entry.type == 'expense',
                    Entry.date >= ninety_days_ago
                )
            ).group_by(Entry.category_id, Category.name).all()

            for cat_id, cat_name, total in category_results:
                category_spending[cat_id] = {
                    'name': cat_name,
                    'monthly_average': float(total) / 3,
                    'total_90_days': float(total)
                }

            return {
                'avg_monthly_income': float(avg_monthly_income),
                'avg_monthly_expenses': float(avg_monthly_expenses),
                'avg_monthly_savings': float(avg_monthly_savings),
                'category_spending': category_spending,
                'baseline_date': datetime.utcnow().isoformat(),
                'data_period_days': 90
            }

        except Exception as e:
            logger.error(f"Error getting baseline data: {str(e)}")
            return {
                'avg_monthly_income': 0,
                'avg_monthly_expenses': 0,
                'avg_monthly_savings': 0,
                'category_spending': {},
                'error': str(e)
            }

    def _calculate_spending_reduction_outcome(
        self,
        user_id: int,
        parameters: Dict,
        baseline_data: Dict
    ) -> Dict:
        """
        Calculate outcome for spending reduction scenario

        Parameters:
            category_id: Category to reduce
            reduction_percent: Percentage to reduce (1-100)
            duration_months: How many months to maintain (default: 6)
        """
        try:
            category_id = parameters['category_id']
            reduction_percent = parameters['reduction_percent']
            duration_months = parameters.get('duration_months', 6)

            # Get category baseline spending
            category_data = baseline_data['category_spending'].get(category_id)
            if not category_data:
                return {
                    'error': 'No spending data for this category',
                    'monthly_savings': 0,
                    'total_savings': 0
                }

            # Calculate savings
            monthly_category_spending = category_data['monthly_average']
            monthly_reduction = monthly_category_spending * (reduction_percent / 100)
            new_monthly_spending = monthly_category_spending - monthly_reduction

            # Calculate total savings
            total_savings = monthly_reduction * duration_months

            # Generate timeline
            timeline = []
            cumulative_savings = 0
            start_date = datetime.utcnow()

            for month in range(duration_months):
                month_date = start_date + timedelta(days=30 * month)
                cumulative_savings += monthly_reduction

                timeline.append({
                    'month': month + 1,
                    'date': month_date.strftime('%Y-%m'),
                    'category_spending': float(new_monthly_spending),
                    'savings_this_month': float(monthly_reduction),
                    'cumulative_savings': float(cumulative_savings),
                    'total_expenses': float(baseline_data['avg_monthly_expenses'] - monthly_reduction)
                })

            # Generate insights
            insights = self._generate_spending_reduction_insights(
                category_data['name'],
                reduction_percent,
                monthly_reduction,
                total_savings,
                duration_months
            )

            return {
                'monthly_savings': float(monthly_reduction),
                'total_savings': float(total_savings),
                'duration_months': duration_months,
                'category_name': category_data['name'],
                'old_monthly_spending': float(monthly_category_spending),
                'new_monthly_spending': float(new_monthly_spending),
                'reduction_amount': float(monthly_reduction),
                'timeline': timeline,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error calculating spending reduction: {str(e)}")
            return {'error': str(e)}

    def _calculate_income_increase_outcome(
        self,
        user_id: int,
        parameters: Dict,
        baseline_data: Dict
    ) -> Dict:
        """
        Calculate outcome for income increase scenario

        Parameters:
            amount: Additional income amount
            frequency: 'monthly', 'biweekly', 'weekly', 'one_time'
            start_date: When increase starts (optional)
            duration_months: How long to project (default: 12)
        """
        try:
            amount = parameters['amount']
            frequency = parameters['frequency']
            duration_months = parameters.get('duration_months', 12)
            start_date = parameters.get('start_date', datetime.utcnow().isoformat())

            # Convert to monthly amount
            frequency_multiplier = {
                'monthly': 1,
                'biweekly': 26 / 12,  # 26 biweekly periods / 12 months
                'weekly': 52 / 12,    # 52 weeks / 12 months
                'one_time': 1 / duration_months
            }

            monthly_increase = amount * frequency_multiplier.get(frequency, 1)

            # Calculate total increase
            total_increase = monthly_increase * duration_months

            # Calculate new financial state
            new_monthly_income = baseline_data['avg_monthly_income'] + monthly_increase
            new_monthly_savings = baseline_data['avg_monthly_savings'] + monthly_increase

            # Generate timeline
            timeline = []
            cumulative_increase = 0

            for month in range(duration_months):
                month_date = datetime.fromisoformat(start_date.replace('Z', '+00:00')) + timedelta(days=30 * month)
                cumulative_increase += monthly_increase

                timeline.append({
                    'month': month + 1,
                    'date': month_date.strftime('%Y-%m'),
                    'income': float(new_monthly_income),
                    'additional_income': float(monthly_increase),
                    'cumulative_increase': float(cumulative_increase),
                    'projected_savings': float(new_monthly_savings)
                })

            # Generate insights
            insights = self._generate_income_increase_insights(
                amount,
                frequency,
                monthly_increase,
                total_increase,
                new_monthly_savings,
                duration_months
            )

            return {
                'monthly_increase': float(monthly_increase),
                'total_increase': float(total_increase),
                'duration_months': duration_months,
                'frequency': frequency,
                'old_monthly_income': float(baseline_data['avg_monthly_income']),
                'new_monthly_income': float(new_monthly_income),
                'old_monthly_savings': float(baseline_data['avg_monthly_savings']),
                'new_monthly_savings': float(new_monthly_savings),
                'timeline': timeline,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error calculating income increase: {str(e)}")
            return {'error': str(e)}

    def _calculate_goal_based_outcome(
        self,
        user_id: int,
        parameters: Dict,
        baseline_data: Dict
    ) -> Dict:
        """
        Calculate if a savings goal is achievable and how

        Parameters:
            target_amount: Goal amount to save
            timeframe_months: Timeframe to achieve goal
            category_adjustments: Optional list of category reductions
        """
        try:
            target_amount = parameters['target_amount']
            timeframe_months = parameters['timeframe_months']
            category_adjustments = parameters.get('category_adjustments', [])

            # Calculate required monthly savings
            required_monthly_savings = target_amount / timeframe_months

            # Current monthly savings
            current_monthly_savings = baseline_data['avg_monthly_savings']

            # Calculate gap
            monthly_gap = required_monthly_savings - current_monthly_savings

            # Check if achievable with current savings
            achievable_with_current = monthly_gap <= 0

            # If not achievable, calculate needed reductions
            total_reduction_needed = 0
            suggested_adjustments = []

            if not achievable_with_current:
                total_reduction_needed = monthly_gap

                # If no adjustments provided, suggest proportional reductions
                if not category_adjustments:
                    category_adjustments = self._suggest_category_adjustments(
                        baseline_data['category_spending'],
                        total_reduction_needed
                    )

            # Calculate outcome with adjustments
            total_monthly_reduction = 0
            adjustment_details = []

            for adj in category_adjustments:
                cat_id = adj['category_id']
                reduction_percent = adj['reduction_percent']

                cat_data = baseline_data['category_spending'].get(cat_id)
                if cat_data:
                    reduction = cat_data['monthly_average'] * (reduction_percent / 100)
                    total_monthly_reduction += reduction

                    adjustment_details.append({
                        'category_id': cat_id,
                        'category_name': cat_data['name'],
                        'reduction_percent': reduction_percent,
                        'monthly_reduction': float(reduction),
                        'old_spending': float(cat_data['monthly_average']),
                        'new_spending': float(cat_data['monthly_average'] - reduction)
                    })

            # New projected savings
            new_monthly_savings = current_monthly_savings + total_monthly_reduction
            goal_achievable = new_monthly_savings >= required_monthly_savings

            # Generate timeline
            timeline = []
            cumulative_savings = 0

            for month in range(timeframe_months):
                month_date = datetime.utcnow() + timedelta(days=30 * month)
                cumulative_savings += new_monthly_savings

                timeline.append({
                    'month': month + 1,
                    'date': month_date.strftime('%Y-%m'),
                    'monthly_savings': float(new_monthly_savings),
                    'cumulative_savings': float(cumulative_savings),
                    'progress_percent': float(min(100, (cumulative_savings / target_amount) * 100))
                })

            # Calculate when goal will be achieved
            months_to_goal = None
            if new_monthly_savings > 0:
                months_to_goal = target_amount / new_monthly_savings

            # Generate insights
            insights = self._generate_goal_based_insights(
                target_amount,
                timeframe_months,
                required_monthly_savings,
                current_monthly_savings,
                new_monthly_savings,
                goal_achievable,
                months_to_goal,
                adjustment_details
            )

            return {
                'target_amount': float(target_amount),
                'timeframe_months': timeframe_months,
                'required_monthly_savings': float(required_monthly_savings),
                'current_monthly_savings': float(current_monthly_savings),
                'new_monthly_savings': float(new_monthly_savings),
                'monthly_gap': float(monthly_gap),
                'goal_achievable': goal_achievable,
                'months_to_goal': float(months_to_goal) if months_to_goal else None,
                'adjustments': adjustment_details,
                'total_monthly_reduction': float(total_monthly_reduction),
                'timeline': timeline,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error calculating goal-based outcome: {str(e)}")
            return {'error': str(e)}

    def _calculate_category_adjustment_outcome(
        self,
        user_id: int,
        parameters: Dict,
        baseline_data: Dict
    ) -> Dict:
        """
        Calculate outcome for multiple category adjustments

        Parameters:
            adjustments: List of {category_id, adjustment_percent}
                        Positive = increase, Negative = decrease
            duration_months: How long to maintain (default: 6)
        """
        try:
            adjustments = parameters.get('adjustments', [])
            duration_months = parameters.get('duration_months', 6)

            total_change = 0
            adjustment_details = []

            for adj in adjustments:
                cat_id = adj['category_id']
                adjustment_percent = adj['adjustment_percent']

                cat_data = baseline_data['category_spending'].get(cat_id)
                if cat_data:
                    change = cat_data['monthly_average'] * (adjustment_percent / 100)
                    total_change += change

                    adjustment_details.append({
                        'category_id': cat_id,
                        'category_name': cat_data['name'],
                        'adjustment_percent': adjustment_percent,
                        'monthly_change': float(change),
                        'old_spending': float(cat_data['monthly_average']),
                        'new_spending': float(cat_data['monthly_average'] + change)
                    })

            # Calculate new financial state
            new_monthly_expenses = baseline_data['avg_monthly_expenses'] + total_change
            new_monthly_savings = baseline_data['avg_monthly_savings'] - total_change

            # Generate timeline
            timeline = []
            cumulative_savings_change = 0

            for month in range(duration_months):
                month_date = datetime.utcnow() + timedelta(days=30 * month)
                cumulative_savings_change += (-total_change)

                timeline.append({
                    'month': month + 1,
                    'date': month_date.strftime('%Y-%m'),
                    'total_expenses': float(new_monthly_expenses),
                    'monthly_savings': float(new_monthly_savings),
                    'cumulative_impact': float(cumulative_savings_change)
                })

            # Generate insights
            insights = self._generate_category_adjustment_insights(
                adjustment_details,
                total_change,
                new_monthly_savings,
                duration_months
            )

            return {
                'total_monthly_change': float(total_change),
                'total_impact': float(total_change * duration_months),
                'duration_months': duration_months,
                'adjustments': adjustment_details,
                'old_monthly_expenses': float(baseline_data['avg_monthly_expenses']),
                'new_monthly_expenses': float(new_monthly_expenses),
                'old_monthly_savings': float(baseline_data['avg_monthly_savings']),
                'new_monthly_savings': float(new_monthly_savings),
                'timeline': timeline,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error calculating category adjustment: {str(e)}")
            return {'error': str(e)}

    def _suggest_category_adjustments(self, category_spending: Dict, target_reduction: float) -> List[Dict]:
        """Suggest proportional category reductions to reach target"""
        suggestions = []

        # Sort categories by spending (highest first)
        sorted_cats = sorted(
            category_spending.items(),
            key=lambda x: x[1]['monthly_average'],
            reverse=True
        )

        # Suggest 20-30% reduction on top spending categories
        remaining_reduction = target_reduction

        for cat_id, cat_data in sorted_cats:
            if remaining_reduction <= 0:
                break

            # Suggest 20% reduction
            reduction_percent = 20
            reduction_amount = cat_data['monthly_average'] * 0.2

            if reduction_amount > remaining_reduction:
                # Adjust percent to match remaining
                reduction_percent = (remaining_reduction / cat_data['monthly_average']) * 100

            suggestions.append({
                'category_id': cat_id,
                'reduction_percent': round(reduction_percent, 1)
            })

            remaining_reduction -= reduction_amount

        return suggestions

    def _generate_spending_reduction_insights(
        self,
        category_name: str,
        reduction_percent: float,
        monthly_savings: float,
        total_savings: float,
        duration_months: int
    ) -> List[str]:
        """Generate AI insights for spending reduction scenario"""
        insights = []

        insights.append(f"Reducing {category_name} spending by {reduction_percent}% will save ${monthly_savings:.2f} per month")
        insights.append(f"Total savings over {duration_months} months: ${total_savings:.2f}")

        if monthly_savings >= 100:
            insights.append(f"This significant reduction could help you reach savings goals {duration_months} faster")

        if reduction_percent >= 50:
            insights.append(f"⚠️ {reduction_percent}% reduction is substantial - ensure this is sustainable long-term")

        return insights

    def _generate_income_increase_insights(
        self,
        amount: float,
        frequency: str,
        monthly_increase: float,
        total_increase: float,
        new_monthly_savings: float,
        duration_months: int
    ) -> List[str]:
        """Generate AI insights for income increase scenario"""
        insights = []

        insights.append(f"Additional {frequency} income of ${amount:.2f} equals ${monthly_increase:.2f} per month")
        insights.append(f"Total additional income over {duration_months} months: ${total_increase:.2f}")

        if new_monthly_savings > 0:
            insights.append(f"New monthly savings potential: ${new_monthly_savings:.2f}")
        else:
            insights.append(f"⚠️ Even with increased income, monthly expenses exceed income by ${abs(new_monthly_savings):.2f}")

        return insights

    def _generate_goal_based_insights(
        self,
        target: float,
        timeframe: int,
        required: float,
        current: float,
        new_savings: float,
        achievable: bool,
        months_to_goal: Optional[float],
        adjustments: List[Dict]
    ) -> List[str]:
        """Generate AI insights for goal-based scenario"""
        insights = []

        insights.append(f"Goal: Save ${target:.2f} in {timeframe} months")
        insights.append(f"Required monthly savings: ${required:.2f}")

        if achievable:
            insights.append(f"✅ Goal is achievable with suggested adjustments!")
            if months_to_goal and months_to_goal < timeframe:
                insights.append(f"You could reach this goal in {months_to_goal:.1f} months")
        else:
            gap = required - new_savings
            insights.append(f"⚠️ Additional ${gap:.2f}/month needed to reach goal")

        if adjustments:
            insights.append(f"Adjusting {len(adjustments)} categories to optimize savings")

        return insights

    def _generate_category_adjustment_insights(
        self,
        adjustments: List[Dict],
        total_change: float,
        new_savings: float,
        duration: int
    ) -> List[str]:
        """Generate AI insights for category adjustment scenario"""
        insights = []

        increases = [a for a in adjustments if a['monthly_change'] > 0]
        decreases = [a for a in adjustments if a['monthly_change'] < 0]

        if decreases:
            total_reduction = sum(abs(a['monthly_change']) for a in decreases)
            insights.append(f"Reducing spending in {len(decreases)} categories saves ${total_reduction:.2f}/month")

        if increases:
            total_increase = sum(a['monthly_change'] for a in increases)
            insights.append(f"Increasing spending in {len(increases)} categories adds ${total_increase:.2f}/month")

        net_impact = -total_change
        if net_impact > 0:
            insights.append(f"Net positive impact: ${net_impact:.2f}/month savings")
        else:
            insights.append(f"Net negative impact: ${abs(net_impact):.2f}/month additional spending")

        insights.append(f"Over {duration} months, total impact: ${net_impact * duration:.2f}")

        return insights

    def get_user_scenarios(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """Get all scenarios for a user"""
        try:
            query = self.db.query(Scenario).filter(Scenario.user_id == user_id)

            if active_only:
                query = query.filter(Scenario.is_active == True)

            scenarios = query.order_by(desc(Scenario.created_at)).all()

            return [s.to_dict() for s in scenarios]

        except Exception as e:
            logger.error(f"Error getting user scenarios: {str(e)}")
            return []

    def get_scenario(self, scenario_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific scenario"""
        try:
            scenario = self.db.query(Scenario).filter(
                and_(
                    Scenario.id == scenario_id,
                    Scenario.user_id == user_id
                )
            ).first()

            return scenario.to_dict() if scenario else None

        except Exception as e:
            logger.error(f"Error getting scenario: {str(e)}")
            return None

    def update_scenario(self, scenario_id: int, user_id: int, updates: Dict) -> Dict:
        """Update scenario (name, description, is_favorite, is_active)"""
        try:
            scenario = self.db.query(Scenario).filter(
                and_(
                    Scenario.id == scenario_id,
                    Scenario.user_id == user_id
                )
            ).first()

            if not scenario:
                return {'success': False, 'error': 'Scenario not found'}

            # Update allowed fields
            allowed_updates = ['name', 'description', 'is_favorite', 'is_active']
            for key, value in updates.items():
                if key in allowed_updates:
                    setattr(scenario, key, value)

            scenario.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(scenario)

            return {
                'success': True,
                'scenario': scenario.to_dict()
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating scenario: {str(e)}")
            return {'success': False, 'error': str(e)}

    def delete_scenario(self, scenario_id: int, user_id: int) -> Dict:
        """Delete a scenario"""
        try:
            scenario = self.db.query(Scenario).filter(
                and_(
                    Scenario.id == scenario_id,
                    Scenario.user_id == user_id
                )
            ).first()

            if not scenario:
                return {'success': False, 'error': 'Scenario not found'}

            self.db.delete(scenario)
            self.db.commit()

            return {'success': True, 'message': 'Scenario deleted'}

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting scenario: {str(e)}")
            return {'success': False, 'error': str(e)}

    def compare_scenarios(
        self,
        user_id: int,
        scenario_ids: List[int],
        comparison_name: Optional[str] = None,
        save_comparison: bool = False
    ) -> Dict:
        """
        Compare multiple scenarios side-by-side

        Args:
            user_id: User ID
            scenario_ids: List of scenario IDs to compare (2-4 scenarios)
            comparison_name: Optional name for saved comparison
            save_comparison: Whether to save comparison to database

        Returns:
            Comparison data with winner and insights
        """
        try:
            if len(scenario_ids) < 2:
                return {'success': False, 'error': 'Need at least 2 scenarios to compare'}

            if len(scenario_ids) > 4:
                return {'success': False, 'error': 'Cannot compare more than 4 scenarios'}

            # Fetch scenarios
            scenarios = self.db.query(Scenario).filter(
                and_(
                    Scenario.id.in_(scenario_ids),
                    Scenario.user_id == user_id
                )
            ).all()

            if len(scenarios) != len(scenario_ids):
                return {'success': False, 'error': 'Some scenarios not found'}

            # Compare scenarios
            comparison_data = []

            for scenario in scenarios:
                outcome = scenario.projected_outcome or {}

                comparison_data.append({
                    'id': scenario.id,
                    'name': scenario.name,
                    'type': scenario.scenario_type,
                    'monthly_impact': outcome.get('monthly_savings') or outcome.get('monthly_increase') or outcome.get('new_monthly_savings', 0),
                    'total_impact': outcome.get('total_savings') or outcome.get('total_increase', 0),
                    'achievable': outcome.get('goal_achievable', True),
                    'months_to_goal': outcome.get('months_to_goal'),
                    'insights': outcome.get('insights', [])
                })

            # Determine winner (highest total impact)
            winner = max(comparison_data, key=lambda x: x['total_impact'] or 0)

            # Generate comparison insights
            insights = self._generate_comparison_insights(comparison_data, winner)

            result = {
                'success': True,
                'scenarios': comparison_data,
                'winner': {
                    'scenario_id': winner['id'],
                    'scenario_name': winner['name'],
                    'reason': f"Highest total impact: ${winner['total_impact']:.2f}"
                },
                'insights': insights
            }

            # Save comparison if requested
            if save_comparison:
                comparison = ScenarioComparison(
                    user_id=user_id,
                    name=comparison_name or f"Comparison of {len(scenario_ids)} scenarios",
                    scenario_ids=scenario_ids,
                    comparison_data=result
                )

                self.db.add(comparison)
                self.db.commit()
                self.db.refresh(comparison)

                result['comparison_id'] = comparison.id

            return result

        except Exception as e:
            logger.error(f"Error comparing scenarios: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _generate_comparison_insights(self, scenarios: List[Dict], winner: Dict) -> List[str]:
        """Generate insights for scenario comparison"""
        insights = []

        # Compare total impacts
        impacts = [s['total_impact'] or 0 for s in scenarios]
        max_impact = max(impacts)
        min_impact = min(impacts)

        if max_impact > min_impact:
            diff = max_impact - min_impact
            insights.append(f"Best scenario outperforms worst by ${diff:.2f}")

        # Check for achievable goals
        achievable = [s for s in scenarios if s.get('achievable', True)]
        if len(achievable) < len(scenarios):
            insights.append(f"⚠️ {len(scenarios) - len(achievable)} scenario(s) may not achieve stated goals")

        # Compare months to goal
        goals_with_timeline = [s for s in scenarios if s.get('months_to_goal')]
        if goals_with_timeline:
            fastest = min(goals_with_timeline, key=lambda x: x['months_to_goal'])
            insights.append(f"Fastest path to goal: {fastest['name']} in {fastest['months_to_goal']:.1f} months")

        return insights

    def get_saved_comparisons(self, user_id: int) -> List[Dict]:
        """Get user's saved scenario comparisons"""
        try:
            comparisons = self.db.query(ScenarioComparison).filter(
                ScenarioComparison.user_id == user_id
            ).order_by(desc(ScenarioComparison.created_at)).all()

            return [c.to_dict() for c in comparisons]

        except Exception as e:
            logger.error(f"Error getting saved comparisons: {str(e)}")
            return []
