# Phase 29: Payment History & Auto-Linking

## Overview
Phase 29 builds on Phase 28's user-managed bills & subscriptions system by adding **payment history tracking** and **intelligent auto-linking suggestions**. Users can now track when they actually paid their bills, view payment history over time, and get AI-powered suggestions to link expense entries to recurring payments.

## Key Features

### 1. Payment History Tracking
Users can now record and track actual payment occurrences:
- **Record Payments**: Log when bills were actually paid
- **Late Payment Tracking**: Automatically detect and flag late payments
- **Skip Payments**: Mark payments that were intentionally skipped
- **Payment Statistics**: View payment reliability metrics
- **Link to Entries**: Connect payments to expense entries

### 2. Auto-Linking Suggestions
AI analyzes expense entries and suggests which ones might be bill payments:
- **Smart Matching**: Based on amount, category, date, and description
- **Confidence Scoring**: Each suggestion includes a confidence percentage
- **One-Click Accept**: Quickly accept suggestions to create payment records
- **Dismissal System**: Dismiss incorrect suggestions
- **Match Explanations**: See why the AI thinks entries match

## Technical Implementation

### Database Models
**File**: `app/models/payment_history.py`

**PaymentOccurrence Model**:
```python
class PaymentOccurrence(Base):
    """Records each actual payment of a recurring bill/subscription"""
    __tablename__ = "payment_occurrences"

    id: Mapped[int]
    user_id: Mapped[int]
    recurring_payment_id: Mapped[int]

    # Payment details
    scheduled_date: Mapped[date]  # When it was supposed to be paid
    actual_date: Mapped[date | None]  # When actually paid
    amount: Mapped[Decimal]
    currency_code: Mapped[str]

    # Status flags
    is_paid: Mapped[bool]
    is_skipped: Mapped[bool]
    is_late: Mapped[bool]

    # Linking
    linked_entry_id: Mapped[int | None]  # Link to expense entry

    # Metadata
    note: Mapped[str | None]
    confirmation_number: Mapped[str | None]
    paid_at: Mapped[datetime | None]
```

**PaymentLinkSuggestion Model**:
```python
class PaymentLinkSuggestion(Base):
    """AI-generated suggestions for linking entries to payments"""
    __tablename__ = "payment_link_suggestions"

    id: Mapped[int]
    user_id: Mapped[int]
    recurring_payment_id: Mapped[int]
    entry_id: Mapped[int]

    # Suggestion quality
    confidence_score: Mapped[float]  # 0.0 to 1.0
    match_reason: Mapped[str]  # JSON explaining the match

    # Status
    is_dismissed: Mapped[bool]
    is_accepted: Mapped[bool]

    # Timestamps
    created_at: Mapped[datetime]
    dismissed_at: Mapped[datetime | None]
    accepted_at: Mapped[datetime | None]
```

### Service Layer
**File**: `app/services/payment_history_service.py`

**PaymentHistoryService Methods**:

**Payment Management**:
- `record_payment()` - Record an actual payment occurrence
- `skip_payment()` - Mark a payment as intentionally skipped
- `link_payment_to_entry()` - Connect payment to expense entry
- `get_payment_history()` - Query payment history with filters
- `get_payment_statistics()` - Calculate payment reliability metrics

**Auto-Linking**:
- `generate_link_suggestions()` - Analyze entries and create suggestions
- `_calculate_match_score()` - Calculate confidence score for entry-payment match
- `get_active_suggestions()` - Get pending suggestions for user
- `accept_suggestion()` - Accept suggestion and create payment occurrence
- `dismiss_suggestion()` - Dismiss incorrect suggestion

**Match Scoring Algorithm**:
```python
def _calculate_match_score(payment, entry) -> tuple[float, Dict]:
    """
    Calculate match confidence based on multiple factors:

    - Amount Similarity (40% weight): How close amounts match
    - Category Match (30% weight): Same category or not
    - Date Proximity (20% weight): How close to due date
    - Description Match (10% weight): Keywords in description

    Returns confidence score 0.0 to 1.0 and match reasons
    """
    score = 0.0
    reasons = []

    # Amount similarity (40%)
    amount_diff = abs(payment.amount - entry.amount)
    amount_similarity = max(0, 1 - (amount_diff / payment.amount))
    score += amount_similarity * 0.4

    # Category match (30%)
    if entry.category_id == payment.category_id:
        score += 0.3
        reasons.append("Category matches")

    # Date proximity (20%)
    next_due = calculate_next_due_date(payment, entry.date)
    days_diff = abs((entry.date - next_due).days)
    if days_diff <= 3:
        date_score = 1.0 - (days_diff / 7)
        score += date_score * 0.2

    # Description match (10%)
    if entry.note and payment.name.lower() in entry.note.lower():
        score += 0.1

    return min(score, 1.0), reasons
```

### API Endpoints
**File**: `app/api/v1/payment_history.py`

**Payment Occurrence Endpoints**:
- `POST /api/v1/payment-history/record` - Record payment
- `POST /api/v1/payment-history/skip` - Mark payment as skipped
- `POST /api/v1/payment-history/link-to-entry` - Link to entry
- `GET /api/v1/payment-history/history` - Get payment history
- `GET /api/v1/payment-history/statistics` - Get payment stats
- `DELETE /api/v1/payment-history/occurrences/{id}` - Delete occurrence

**Auto-Linking Endpoints**:
- `POST /api/v1/payment-history/generate-suggestions` - Generate suggestions
- `GET /api/v1/payment-history/suggestions` - Get active suggestions
- `POST /api/v1/payment-history/suggestions/{id}/accept` - Accept suggestion
- `POST /api/v1/payment-history/suggestions/{id}/dismiss` - Dismiss suggestion

**Request/Response Models** (Pydantic):
```python
class RecordPaymentRequest(BaseModel):
    recurring_payment_id: int
    scheduled_date: date
    actual_date: date
    amount: float
    currency_code: str = "USD"
    linked_entry_id: Optional[int] = None
    note: Optional[str] = None
    confirmation_number: Optional[str] = None

class SkipPaymentRequest(BaseModel):
    recurring_payment_id: int
    scheduled_date: date
    note: Optional[str] = None
```

### Database Migration
**File**: `alembic/versions/f3c5d1a8e9b2_add_payment_history_and_auto_linking_phase_29.py`

**Migration Details**:
- Creates `payment_occurrences` table
- Creates `payment_link_suggestions` table
- Adds foreign key constraints with proper cascading
- Creates indexes for performance

```python
def upgrade() -> None:
    # Create payment_occurrences table
    op.create_table(
        'payment_occurrences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recurring_payment_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('actual_date', sa.Date(), nullable=True),
        # ... other columns
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recurring_payment_id'], ['recurring_payments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['linked_entry_id'], ['entries.id'], ondelete='SET NULL')
    )
    op.create_index('ix_payment_occurrences_user_id', ...)
    op.create_index('ix_payment_occurrences_scheduled_date', ...)

    # Create payment_link_suggestions table
    op.create_table('payment_link_suggestions', ...)
```

### Model Relationships

**User Model** (`app/models/user.py`):
```python
# Payment history relationships - Phase 29
payment_occurrences = relationship("PaymentOccurrence", back_populates="owner", ...)
payment_link_suggestions = relationship("PaymentLinkSuggestion", back_populates="owner", ...)
```

**RecurringPayment Model** (`app/models/recurring_payment.py`):
```python
# Phase 29 relationship
occurrences = relationship("PaymentOccurrence", back_populates="recurring_payment", ...)
```

### UI Integration
**File**: `app/api/v1/intelligence_pages.py`

The bills & subscriptions page now includes:
- Auto-linking suggestions passed to template
- Payment history service initialized
- Suggestions displayed with confidence scores

```python
@router.get("/bills-subscriptions")
def bills_subscriptions_page(...):
    payment_service = RecurringPaymentService(db)
    history_service = PaymentHistoryService(db)

    # Get auto-linking suggestions (Phase 29)
    suggestions = history_service.get_active_suggestions(user.id, min_confidence=0.6)

    return render(..., {
        ...,
        "link_suggestions": suggestions,  # Phase 29
    })
```

## User Experience

### Recording a Payment
1. User navigates to Bills & Subscriptions page
2. Clicks "Mark as Paid" on a bill
3. Modal opens with payment details pre-filled
4. User can:
   - Confirm payment date (defaults to today)
   - Enter confirmation number
   - Add notes
   - Link to an existing expense entry
5. Clicks "Record Payment"
6. Payment history is updated
7. Statistics reflect the new payment

### Auto-Linking Workflow
1. User adds expense entries as usual
2. System automatically analyzes entries nightly (or on-demand)
3. Generates suggestions for entries that match recurring payments
4. User sees suggestions banner on Bills page:
   - "We found 3 entries that might be bill payments"
5. Each suggestion shows:
   - Recurring payment name
   - Entry amount and date
   - Confidence score (e.g., "85% match")
   - Match reasons (e.g., "Amount matches, same category, 1 day from due date")
6. User can:
   - **Accept**: Creates payment occurrence and links entry
   - **Dismiss**: Hides suggestion permanently
   - **View Details**: See full entry and payment information

### Payment Statistics
Users can view:
- **Total Payments**: Count of payments made
- **On-Time Rate**: Percentage paid on time
- **Late Payments**: Count of late payments
- **Skipped Payments**: Intentionally skipped payments
- **Average Amount**: Average payment amount
- **Payment Trends**: Chart showing payment reliability over time

## Data Flow

### Payment Recording:
```
User Action → POST /api/v1/payment-history/record
→ PaymentHistoryService.record_payment()
→ Create PaymentOccurrence
→ Set is_late flag if actual_date > scheduled_date
→ Link to entry if provided
→ Return success with occurrence_id
```

### Auto-Linking Generation:
```
Scheduled Task / Manual Trigger
→ POST /api/v1/payment-history/generate-suggestions
→ PaymentHistoryService.generate_link_suggestions()
→ Query unlinked expense entries (last 30 days)
→ For each recurring payment:
    → For each entry:
        → Calculate match score
        → If score >= 0.6:
            → Create PaymentLinkSuggestion
→ Return count of suggestions created
```

### Accepting Suggestion:
```
User Clicks Accept
→ POST /api/v1/payment-history/suggestions/{id}/accept
→ PaymentHistoryService.accept_suggestion()
→ Create PaymentOccurrence with linked_entry_id
→ Mark suggestion as accepted
→ Return success with occurrence_id
```

## Security Considerations

### Authorization
- All endpoints require authentication
- Users can only access their own payment occurrences
- Payment ownership verified on every operation
- Entry ownership validated before linking

### Validation
- Pydantic models validate all input
- Amounts must be positive
- Dates validated for logical consistency
- Confidence scores bounded 0.0 to 1.0

### Data Integrity
- Foreign key constraints ensure referential integrity
- CASCADE deletes remove occurrences when payment deleted
- SET NULL preserves history when entry deleted
- Transactions ensure atomic operations

## Performance Optimizations

1. **Indexed Queries**:
   - Index on `user_id` for user payment lookup
   - Index on `scheduled_date` for date range queries
   - Index on `linked_entry_id` for entry lookup
   - Index on `created_at` for suggestion sorting

2. **Batch Processing**:
   - Suggestion generation processes in batches
   - Analyzes multiple payments/entries efficiently
   - Minimizes database round trips

3. **Caching Opportunities** (Future):
   - Cache payment statistics
   - Cache active suggestion counts
   - Invalidate on payment updates

4. **Query Optimization**:
   - Filters applied at database level
   - Only fetch necessary columns
   - Use joins efficiently

## Testing Recommendations

### Unit Tests
- Test payment recording with various scenarios
- Test late payment detection logic
- Test match scoring algorithm
- Test suggestion generation
- Test accept/dismiss workflows

### Integration Tests
- Test API endpoints with authentication
- Test payment history queries
- Test auto-linking full workflow
- Test statistics calculation
- Test concurrent operations

### UI Tests
- Test payment recording modal
- Test suggestion acceptance workflow
- Test dismissal functionality
- Test payment history display
- Test statistics visualization

## Known Limitations

1. **No Bulk Recording**: Can't record multiple payments at once
2. **No Payment Editing**: Once recorded, payments can only be deleted
3. **No Recurring Patterns**: Doesn't detect new recurring payments automatically
4. **Single Currency**: Each payment has one currency (no multi-currency)
5. **Manual Suggestion Generation**: Not fully automated (requires trigger)
6. **No Payment Methods**: Doesn't track credit card vs bank account
7. **No Receipt Storage**: Can't attach receipt images

## Future Enhancements

### Phase 30+ Features
1. **Calendar Integration**: Bills & subscriptions appear on calendar view at their due dates
   - Users see all upcoming bills when viewing the calendar
   - Visual representation of payment due dates
   - Click on calendar entries to view payment details
   - Color-coded by payment status (paid, pending, overdue)
2. **Payment Analytics Dashboard**: Comprehensive payment trends visualization
3. **Bulk Payment Recording**: Record multiple payments at once
4. **Payment Reminders**: Proactive reminders based on history
5. **Automatic Suggestion Generation**: Daily background job
6. **Payment Forecasting**: Predict future payment amounts (utilities)
7. **Receipt Upload**: Attach receipts to payment occurrences
8. **Payment Methods**: Track which card/account used
9. **CSV Export**: Export payment history
10. **Variable Amount Tracking**: Handle bills with changing amounts

### Advanced Features
1. **Machine Learning**: Improve match scoring with ML
2. **Pattern Detection**: Detect new recurring payments automatically
3. **Anomaly Detection**: Flag unusual payment amounts
4. **Payment Optimization**: Suggest better payment timing
5. **Bill Negotiation Tracking**: Track negotiation attempts
6. **Payment Groups**: Group related payments (family bills)
7. **Split Payments**: Handle payments split across multiple people
8. **Payment Disputes**: Track disputed charges

## API Documentation

### Record Payment
```http
POST /api/v1/payment-history/record
Content-Type: application/json

{
  "recurring_payment_id": 1,
  "scheduled_date": "2025-11-15",
  "actual_date": "2025-11-15",
  "amount": 15.99,
  "currency_code": "USD",
  "linked_entry_id": 123,
  "note": "Paid on time",
  "confirmation_number": "TXN-12345"
}

Response 200:
{
  "success": true,
  "occurrence_id": 1,
  "is_late": false,
  "message": "Payment recorded successfully"
}
```

### Generate Suggestions
```http
POST /api/v1/payment-history/generate-suggestions?days_back=30

Response 200:
{
  "success": true,
  "suggestions_created": 5,
  "message": "Generated 5 link suggestion(s)"
}
```

### Get Active Suggestions
```http
GET /api/v1/payment-history/suggestions?min_confidence=0.6

Response 200:
{
  "suggestions": [
    {
      "id": 1,
      "recurring_payment_id": 1,
      "recurring_payment_name": "Netflix",
      "entry_id": 123,
      "entry_amount": 15.99,
      "entry_date": "2025-11-15",
      "entry_note": "Netflix subscription",
      "confidence_score": 0.95,
      "match_reasons": [
        "Amount matches closely ($15.99)",
        "Category matches",
        "Date is 0 days from due date"
      ],
      "created_at": "2025-11-24T10:00:00"
    }
  ],
  "count": 1
}
```

### Accept Suggestion
```http
POST /api/v1/payment-history/suggestions/1/accept

Response 200:
{
  "success": true,
  "occurrence_id": 1,
  "message": "Suggestion accepted and payment recorded"
}
```

### Get Payment Statistics
```http
GET /api/v1/payment-history/statistics?months=12

Response 200:
{
  "success": true,
  "statistics": {
    "total_payments": 120,
    "skipped_payments": 2,
    "late_payments": 5,
    "on_time_payments": 115,
    "on_time_rate": 95.83,
    "total_amount_paid": 1919.88,
    "average_payment": 15.99,
    "analysis_period_months": 12
  }
}
```

## Deployment Notes

### Database Migration
```bash
# Apply migration
.venv/Scripts/alembic.exe upgrade head

# Or on production
alembic upgrade head
```

### Environment Variables
- No new environment variables required
- Uses existing database configuration

### Dependencies
- No new Python dependencies
- Uses existing FastAPI, SQLAlchemy, Pydantic

### Breaking Changes
- None - purely additive feature

## Conclusion

Phase 29 successfully delivers payment history tracking and intelligent auto-linking, completing the bills & subscriptions management system. Users can now:
- Track when they actually pay bills
- See payment reliability statistics
- Get AI-powered suggestions to link expenses to bills
- View complete payment history over time

The auto-linking algorithm provides high-quality suggestions by considering multiple factors, and the confidence scoring helps users make informed decisions about accepting suggestions.

This phase provides a solid foundation for advanced payment analytics and forecasting in future phases.

## Files Created/Modified

### New Files
- `app/models/payment_history.py` - Database models
- `app/services/payment_history_service.py` - Business logic
- `app/api/v1/payment_history.py` - REST API endpoints
- `alembic/versions/f3c5d1a8e9b2_*.py` - Database migration
- `docs/PHASE_29_PAYMENT_HISTORY.md` - This documentation

### Modified Files
- `app/models/user.py` - Added payment history relationships
- `app/models/recurring_payment.py` - Added occurrences relationship
- `app/main.py` - Imported new models
- `app/api/routes.py` - Registered payment history router
- `app/api/v1/intelligence_pages.py` - Added suggestions to bills page
