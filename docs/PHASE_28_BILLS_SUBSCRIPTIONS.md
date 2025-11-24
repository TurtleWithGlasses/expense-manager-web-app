# Phase 28: User-Managed Bills & Subscriptions

## Overview
Phase 28 completely redesigns the bills and subscriptions system from an AI-detected approach to a **user-managed system**. Users now explicitly create and configure their recurring payments, select categories, set due dates, and receive AI warnings for upcoming payments. Bills are integrated into the calendar view for better financial planning.

## Key Changes from Previous Implementation

### Previous System (AI-Detected)
- AI automatically detected recurring transactions as bills
- Constant expenditures (food, coffee) were incorrectly flagged as bills
- Users had no control over what was considered a bill
- No unified interface for bills and subscriptions

### New System (User-Managed)
- **Users manually create** bills and subscriptions
- **Users select categories** for each payment
- **Users set due dates** and frequencies
- **AI only warns** about upcoming payments (doesn't detect)
- **Unified interface** for both bills and subscriptions
- **Calendar integration** shows bills on due dates

## Features Implemented

### 1. Recurring Payment Management

**User-Controlled System**:
- Users create and configure their own recurring payments
- Manual category selection prevents misclassification
- Flexible frequency options for different payment schedules
- Pause/resume functionality without deletion
- Full CRUD operations via REST API

**Supported Frequencies**:
- **Weekly** - Bills due on specific day of week (0=Monday, 6=Sunday)
- **Biweekly** - Every 2 weeks from start date
- **Monthly** - Bills due on specific day of month (1-31)
- **Quarterly** - Every 3 months
- **Annually** - Once per year

**Payment Configuration**:
- Name and description
- Amount and currency
- Category assignment (required)
- Due day (day of week or month)
- Start date and optional end date
- Reminder configuration (days before due)

### 2. AI Warnings System

**Role of AI**:
- Generate reminders for upcoming payments
- Warn users about bills to maintain cash flow awareness
- Help prevent missed payments
- **Does NOT auto-detect** bills from transactions

**Reminder Features**:
- Configurable days-before warning (0-30 days)
- Active reminders displayed on bills page
- Dismiss functionality
- Mark-as-paid with optional entry linking
- Days-until-due calculation

### 3. Calendar Integration

**Bill Visualization**:
- Bills appear on calendar with 📅 icon
- Shows due dates within each month
- Displays payment name and amount
- Marked as special "bill" entry type
- Includes frequency information (monthly, weekly, etc.)

**Integration Details**:
- Calendar service queries recurring payments
- Calculates next due date for each payment
- Filters payments that fall within displayed month
- Does not affect income/expense totals
- Purely informational display

### 4. Dark Theme Support

**Consistent Theming**:
- All intelligence pages use dark backgrounds
- Text colors use CSS custom properties
- Cards use `var(--panel)` and `var(--surface)`
- Text uses `var(--text)` and `var(--text-secondary)`
- Readable in both light and dark modes

**Fixed Templates**:
- `intelligence/dashboard.html`
- `intelligence/budget_recommendations.html`
- `intelligence/bills_subscriptions.html`
- `intelligence/duplicates.html`

### 5. Category Management Integration

**Seamless Category Access**:
- Add category button in payment creation modal
- Opens categories page in new tab
- Allows users to add missing categories mid-workflow
- Helper text explains functionality
- Maintains form state when returning

## Technical Implementation

### Database Models
**File**: `app/models/recurring_payment.py`

**RecurringPayment Model**:
```python
class RecurringPayment(Base):
    __tablename__ = "recurring_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    currency_code: Mapped[str] = mapped_column(String(3), default='USD')

    frequency: Mapped[RecurrenceFrequency] = mapped_column(SQLEnum(RecurrenceFrequency))
    due_day: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    remind_days_before: Mapped[int] = mapped_column(Integer, default=3)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="recurring_payments")
    category = relationship("Category", back_populates="recurring_payments")
    reminders = relationship("PaymentReminder", back_populates="payment", cascade="all, delete-orphan")
```

**PaymentReminder Model**:
```python
class PaymentReminder(Base):
    __tablename__ = "payment_reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    recurring_payment_id: Mapped[int] = mapped_column(ForeignKey("recurring_payments.id", ondelete="CASCADE"))

    reminder_date: Mapped[date] = mapped_column(Date, index=True)
    due_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))

    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_entry_id: Mapped[int | None] = mapped_column(ForeignKey("entries.id", ondelete="SET NULL"))

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="payment_reminders")
    payment = relationship("RecurringPayment", back_populates="reminders")
    paid_entry = relationship("Entry", foreign_keys=[paid_entry_id])
```

**Enums**:
```python
class RecurrenceFrequency(enum.Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
```

### Service Layer
**File**: `app/services/recurring_payment_service.py`

**RecurringPaymentService Methods**:

1. **CRUD Operations**:
   - `create_recurring_payment()` - Create new payment
   - `get_user_recurring_payments()` - List user's payments
   - `update_recurring_payment()` - Update payment details
   - `delete_recurring_payment()` - Remove payment
   - `toggle_active_status()` - Pause/resume payment

2. **Due Date Calculation**:
   - `calculate_next_due_date()` - Smart calculation for all frequencies
   - `_next_weekly_due()` - Weekly due date logic
   - `_next_biweekly_due()` - Biweekly due date logic
   - `_next_monthly_due()` - Monthly due date logic with day clamping
   - `_next_quarterly_due()` - Quarterly due date logic
   - `_next_annual_due()` - Annual due date logic

3. **Reminder Management**:
   - `generate_reminders()` - Create upcoming payment reminders
   - `get_active_reminders()` - Get reminders for display
   - `dismiss_reminder()` - User dismisses reminder
   - `mark_reminder_paid()` - Mark reminder as paid

4. **Analytics**:
   - `get_payment_summary()` - Total payments, monthly/annual costs
   - `get_payments_by_category()` - Category breakdown
   - `get_upcoming_payments()` - Payments due soon

**Due Date Calculation Logic**:

```python
def calculate_next_due_date(self, payment: RecurringPayment, after_date: Optional[date] = None) -> Optional[date]:
    """Calculate the next due date for a recurring payment"""
    if after_date is None:
        after_date = date.today()

    # Check if payment has ended
    if payment.end_date and after_date > payment.end_date:
        return None

    # If before start date, return first due date
    if after_date < payment.start_date:
        return self._calculate_first_due_date(payment)

    # Calculate based on frequency
    if payment.frequency == RecurrenceFrequency.WEEKLY:
        return self._next_weekly_due(payment, after_date)
    elif payment.frequency == RecurrenceFrequency.BIWEEKLY:
        return self._next_biweekly_due(payment, after_date)
    elif payment.frequency == RecurrenceFrequency.MONTHLY:
        return self._next_monthly_due(payment, after_date)
    elif payment.frequency == RecurrenceFrequency.QUARTERLY:
        return self._next_quarterly_due(payment, after_date)
    elif payment.frequency == RecurrenceFrequency.ANNUALLY:
        return self._next_annual_due(payment, after_date)
```

**Monthly Due Date with Day Clamping**:
```python
def _next_monthly_due(self, payment: RecurringPayment, after_date: date) -> date:
    """Handle monthly payments with proper day clamping for short months"""
    year = after_date.year
    month = after_date.month

    # Start with next month if past due day
    if after_date.day >= payment.due_day:
        month += 1
        if month > 12:
            month = 1
            year += 1

    # Clamp day to valid range for month
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    actual_day = min(payment.due_day, max_day)

    return date(year, month, actual_day)
```

### API Endpoints
**File**: `app/api/v1/recurring_payments.py`

**CRUD Endpoints**:
- `POST /api/v1/recurring-payments/` - Create payment
- `GET /api/v1/recurring-payments/` - List all payments
- `GET /api/v1/recurring-payments/{payment_id}` - Get specific payment
- `PUT /api/v1/recurring-payments/{payment_id}` - Update payment
- `DELETE /api/v1/recurring-payments/{payment_id}` - Delete payment
- `POST /api/v1/recurring-payments/{payment_id}/toggle` - Pause/resume

**Reminder Endpoints**:
- `POST /api/v1/recurring-payments/generate-reminders` - Generate reminders
- `GET /api/v1/recurring-payments/reminders/active` - Get active reminders
- `POST /api/v1/recurring-payments/reminders/{reminder_id}/dismiss` - Dismiss reminder
- `POST /api/v1/recurring-payments/reminders/{reminder_id}/mark-paid` - Mark as paid

**Summary Endpoint**:
- `GET /api/v1/recurring-payments/summary` - Payment statistics

**Request/Response Models** (Pydantic):
```python
class RecurringPaymentCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    amount: float
    currency_code: str = "USD"
    frequency: str
    due_day: int
    start_date: date
    end_date: Optional[date] = None
    remind_days_before: int = 3

class RecurringPaymentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    currency_code: Optional[str] = None
    frequency: Optional[str] = None
    due_day: Optional[int] = None
    end_date: Optional[date] = None
    remind_days_before: Optional[int] = None
```

### UI Implementation
**File**: `app/templates/intelligence/bills_subscriptions.html`

**Page Structure**:
1. **Header** - Title and "New Bill/Subscription" button
2. **Summary Cards** - Total payments, monthly cost, annual cost
3. **AI Warnings Section** - Upcoming payment alerts
4. **Payments Table** - List of all recurring payments
5. **Add Payment Modal** - Scrollable form for creating payments
6. **Actions** - Edit, delete, pause/resume buttons

**Modal Features**:
- **Scrollable** - Uses `modal-dialog-scrollable` Bootstrap class
- **Category Selection** - Dropdown with all user categories
- **Add Category Button** - Opens categories page in new tab
- **Form Fields**:
  - Name (required)
  - Description (optional)
  - Amount (required, positive)
  - Currency (from user preferences)
  - Frequency (dropdown: weekly/biweekly/monthly/quarterly/annually)
  - Due day (number input)
  - Start date (date picker)
  - End date (optional)
  - Reminder days (0-30)

**JavaScript Functionality**:
```javascript
// Load payments on page load
async function loadPayments() {
    const response = await fetch('/api/v1/recurring-payments/');
    const data = await response.json();
    renderPaymentsTable(data.payments);
}

// Create new payment
async function createPayment(formData) {
    const response = await fetch('/api/v1/recurring-payments/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    });

    if (response.ok) {
        showToast('Payment created successfully', 'success');
        closeModal();
        loadPayments();
    }
}

// Delete payment
async function deletePayment(paymentId) {
    if (!confirm('Are you sure you want to delete this payment?')) return;

    const response = await fetch(`/api/v1/recurring-payments/${paymentId}`, {
        method: 'DELETE'
    });

    if (response.ok) {
        showToast('Payment deleted', 'success');
        loadPayments();
    }
}
```

**Dark Theme CSS**:
```css
.card {
    background-color: var(--panel) !important;
    color: var(--text);
}

.card-header {
    background-color: var(--surface) !important;
    color: var(--text) !important;
}

.table {
    color: var(--text);
}

.modal-content {
    background-color: var(--panel);
    color: var(--text);
}

/* Scrollable modal */
#addPaymentModal .modal-body {
    overflow-y: auto;
    max-height: none;
}
```

### Page Routes
**File**: `app/api/v1/intelligence_pages.py`

**New Route**:
```python
@router.get("/bills-subscriptions", response_class=HTMLResponse)
def bills_subscriptions_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Unified bills & subscriptions management page - User-managed system"""
    payment_service = RecurringPaymentService(db)

    # Get all recurring payments
    payments = payment_service.get_user_recurring_payments(user.id, include_inactive=False)

    # Get active reminders (AI warnings)
    reminders = payment_service.get_active_reminders(user.id, days_ahead=14)

    # Get payment summary
    summary = payment_service.get_payment_summary(user.id)

    # Get user's categories for the form
    categories = db.query(Category).filter(Category.user_id == user.id).order_by(Category.name).all()

    # Format payments with next due dates
    formatted_payments = []
    for payment in payments:
        next_due = payment_service.calculate_next_due_date(payment)
        formatted_payments.append({
            'id': payment.id,
            'name': payment.name,
            'amount': float(payment.amount),
            'frequency': payment.frequency.value,
            'category_name': payment.category.name if payment.category else 'Uncategorized',
            'next_due_date': next_due.isoformat() if next_due else None,
            'days_until_due': (next_due - date.today()).days if next_due else None,
            'is_active': payment.is_active
        })

    currency_ctx = _get_currency_helpers(db, user.id)

    return render(request, "intelligence/bills_subscriptions.html", {
        "user": user,
        "payments": formatted_payments,
        "reminders": reminders,
        "total_payments": summary['total_payments'],
        "total_monthly_cost": summary['total_monthly_cost'],
        "total_annual_cost": summary['total_annual_cost'],
        "categories": categories,
        **currency_ctx,
    })
```

**Backward Compatibility Routes**:
```python
@router.get("/recurring-bills", response_class=HTMLResponse)
def recurring_bills_page_redirect(request: Request):
    """Redirect to unified bills & subscriptions page"""
    return RedirectResponse(url="/intelligence/bills-subscriptions", status_code=301)

@router.get("/subscriptions", response_class=HTMLResponse)
def subscriptions_page_redirect(request: Request):
    """Redirect to unified bills & subscriptions page"""
    return RedirectResponse(url="/intelligence/bills-subscriptions", status_code=301)
```

### Calendar Integration
**File**: `app/services/calendar_service.py`

**Integration Code**:
```python
def get_calendar_data(db: Session, user_id: int, year: int, month: int) -> Dict:
    # ... existing code for regular entries ...

    # Add upcoming bills & subscriptions to calendar
    recurring_service = RecurringPaymentService(db)
    payments = recurring_service.get_user_recurring_payments(user_id, include_inactive=False)

    for payment in payments:
        next_due = recurring_service.calculate_next_due_date(payment, first_day)

        # If due date falls within this month, add it to the calendar
        if next_due and first_day <= next_due <= last_day:
            due_date_str = next_due.isoformat()

            # Initialize date if not exists
            if due_date_str not in dates_data:
                dates_data[due_date_str] = {
                    'income_total': 0.0,
                    'expense_total': 0.0,
                    'net': 0.0,
                    'entry_count': 0,
                    'entries': []
                }

            # Add bill/subscription as a special entry type
            dates_data[due_date_str]['entries'].append({
                'id': f'bill_{payment.id}',
                'type': 'bill',  # Special type for bills
                'amount': float(payment.amount),
                'currency_code': payment.currency_code,
                'category_name': payment.category.name if payment.category else 'Uncategorized',
                'category_icon': '📅',  # Calendar icon for bills
                'note': payment.name,
                'description': f"Due: {payment.name}",
                'is_recurring': True,
                'frequency': payment.frequency.value
            })

    return {
        'year': year,
        'month': month,
        'dates': dates_data
    }
```

### Model Relationships

**User Model** (`app/models/user.py`):
```python
# Recurring payment relationships - Phase 28
recurring_payments = relationship(
    "RecurringPayment",
    back_populates="owner",
    cascade="all, delete-orphan",
    passive_deletes=True
)

payment_reminders = relationship(
    "PaymentReminder",
    back_populates="owner",
    cascade="all, delete-orphan",
    passive_deletes=True
)
```

**Category Model** (`app/models/category.py`):
```python
# Recurring payments relationship - Phase 28
recurring_payments = relationship(
    "RecurringPayment",
    back_populates="category",
    cascade="all, delete-orphan"
)
```

### Database Migration
**File**: `alembic/versions/ae483fa17f81_add_recurring_payments_and_reminders_.py`

**Migration Details**:
- Creates `recurring_payments` table with all fields
- Creates `payment_reminders` table
- Adds foreign key constraints with CASCADE delete
- Adds indexes on user_id and reminder_date
- Creates RecurrenceFrequency enum type

```python
def upgrade() -> None:
    # Create enum type
    op.execute("CREATE TYPE recurrencefrequency AS ENUM ('WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUALLY')")

    # Create recurring_payments table
    op.create_table(
        'recurring_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        # ... other columns ...
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_recurring_payments_user_id'), 'recurring_payments', ['user_id'])

    # Create payment_reminders table
    op.create_table('payment_reminders', ...)
    op.create_index(op.f('ix_payment_reminders_user_id'), 'payment_reminders', ['user_id'])
    op.create_index(op.f('ix_payment_reminders_reminder_date'), 'payment_reminders', ['reminder_date'])

def downgrade() -> None:
    op.drop_table('payment_reminders')
    op.drop_table('recurring_payments')
    op.execute('DROP TYPE recurrencefrequency')
```

## User Experience

### Payment Creation Flow
1. User navigates to `/intelligence/bills-subscriptions`
2. Clicks "New Bill/Subscription" button
3. Modal opens with scrollable form
4. User fills in:
   - Name (e.g., "Netflix Subscription")
   - Category (selects from dropdown or adds new via button)
   - Amount (e.g., 15.99)
   - Frequency (e.g., "Monthly")
   - Due day (e.g., 15 for 15th of each month)
   - Start date
   - Optional: description, end date, reminder days
5. Submits form
6. Success toast appears
7. New payment appears in table
8. Summary cards update with new totals

### AI Warning Interaction
1. System generates reminders X days before due date
2. User sees warning card at top of page:
   - "Netflix due in 3 days - $15.99"
3. User options:
   - **Dismiss** - Remove reminder without action
   - **Mark as Paid** - Record payment made
   - **Ignore** - Let reminder stay until due date passes

### Calendar View
1. User navigates to `/calendar/`
2. Sees month view with all entries
3. Bills appear on due dates with 📅 icon
4. Hover shows bill details
5. Click opens bill details (future enhancement)
6. Bills don't affect income/expense totals
7. Purely visual reminder of upcoming payments

## Data Flow

### Payment Creation:
```
User Form → Frontend Validation → POST /api/v1/recurring-payments/
→ Pydantic Validation → RecurringPaymentService.create_recurring_payment()
→ Database Insert → Return Payment → Update UI
```

### Due Date Calculation:
```
Calendar Service → RecurringPaymentService.get_user_recurring_payments()
→ For each payment → calculate_next_due_date()
→ Check frequency type → Call frequency-specific method
→ Return due date → Add to calendar data
```

### Reminder Generation:
```
Scheduled Task (daily) → RecurringPaymentService.generate_reminders()
→ Get all active payments → Calculate next due dates
→ Check if within reminder window → Create PaymentReminder
→ Store in database → Display on next page load
```

## Security Considerations

### Authorization
- All endpoints require authentication via `current_user` dependency
- Users can only access their own payments and reminders
- Payment ownership verified on every CRUD operation
- Category access validated (user must own category)

### Validation
- Pydantic models validate all input
- Amount must be positive (> 0)
- Currency code must be 3 characters
- Frequency must be valid enum value
- Due day validated based on frequency type
- Start date cannot be in the past (warning only)

### Data Integrity
- Foreign key constraints ensure referential integrity
- CASCADE deletes remove reminders when payment deleted
- CASCADE deletes remove payments when user/category deleted
- Transactions ensure atomic updates
- No orphaned records possible

## Performance Optimizations

1. **Indexed Queries**:
   - Index on `user_id` for fast user payment lookup
   - Index on `reminder_date` for efficient reminder queries
   - Compound indexes considered for future optimization

2. **Lazy Calculation**:
   - Due dates calculated on-demand, not stored
   - Prevents stale data issues
   - Minimal performance impact (simple date math)

3. **Batch Operations**:
   - Reminder generation processes all users in batches
   - Calendar integration fetches all payments at once
   - Reduces database round trips

4. **Caching Opportunities** (Future):
   - Cache formatted payment data for calendar
   - Cache reminder counts for dashboard
   - Invalidate on payment updates

## Testing Recommendations

### Unit Tests
- Test due date calculation for all frequency types
- Test edge cases (end of month, leap years, etc.)
- Test reminder generation logic
- Test payment CRUD operations
- Test status transitions

### Integration Tests
- Test API endpoints with authentication
- Test payment creation with category validation
- Test calendar integration
- Test reminder workflow (create → dismiss → mark paid)
- Test multi-currency support

### UI Tests
- Test modal scrollability
- Test form validation
- Test add category button flow
- Test responsive layout
- Test dark theme styling

## Known Limitations

1. **No Payment History**: Can't track payment occurrences over time
2. **No Auto-Pay**: Users must manually mark payments as made
3. **No Bank Integration**: Can't auto-detect actual payments
4. **No Split Payments**: Can't share bills with others
5. **Single Currency**: Each payment has one currency (no multi-currency bills)
6. **No Payment Methods**: Can't track credit card vs bank account
7. **No Late Fees**: No automatic late fee calculation

## Future Enhancements

### Phase 29+ Features
1. **Payment History**: Track each payment occurrence
2. **Auto-Linking**: Suggest linking entries to bills
3. **Payment Analytics**: Spending trends on recurring vs one-time
4. **Bill Sharing**: Split bills with family/roommates
5. **Payment Methods**: Track which card/account used
6. **Receipt Upload**: Attach receipts to payments
7. **Smart Suggestions**: AI suggests potential recurring payments
8. **Budget Integration**: Compare bills vs budget allocations
9. **Payment Forecasting**: Project future cash flow needs
10. **Bill Negotiation Tips**: AI suggests ways to reduce bills

### Advanced Features
1. **Variable Amounts**: Handle bills that change (utilities)
2. **Proration**: Handle mid-month starts/cancellations
3. **Grace Periods**: Configure late payment windows
4. **Escalation**: Automatic reminders for overdue bills
5. **Bill Comparison**: Compare to average costs
6. **Contract Tracking**: Track subscription term lengths
7. **Cancellation Reminders**: Warn before free trial ends
8. **Payment Automation**: Integration with payment services

## Deployment Notes

### Database Migration
```bash
# Generate migration
alembic revision --autogenerate -m "Add recurring payments and reminders"

# Apply migration
alembic upgrade head
```

### Environment Variables
- No new environment variables required
- Uses existing currency and user preference systems

### Dependencies
- No new Python dependencies
- Uses existing FastAPI, SQLAlchemy, Pydantic
- Frontend uses Bootstrap 5 (already included)

### Breaking Changes
- Old `/intelligence/recurring-bills` route redirects to new unified page
- Old `/intelligence/subscriptions` route redirects to new unified page
- No breaking API changes (new endpoints only)

## Backward Compatibility

### Route Redirects
- `/intelligence/recurring-bills` → `/intelligence/bills-subscriptions` (301)
- `/intelligence/subscriptions` → `/intelligence/bills-subscriptions` (301)

### Data Migration
- No existing data to migrate (new feature)
- If previous bill detection existed, migration script needed to:
  1. Convert AI-detected bills to user-managed payments
  2. Assign default categories
  3. Calculate due dates from transaction patterns
  3. Create initial reminders

## Files Created/Modified

### New Files
- `app/models/recurring_payment.py` - Database models
- `app/services/recurring_payment_service.py` - Business logic
- `app/api/v1/recurring_payments.py` - REST API endpoints
- `app/templates/intelligence/bills_subscriptions.html` - UI page
- `alembic/versions/ae483fa17f81_*.py` - Database migration
- `docs/PHASE_28_BILLS_SUBSCRIPTIONS.md` - This documentation

### Modified Files
- `app/models/user.py` - Added recurring payment relationships
- `app/models/category.py` - Added recurring payment relationship
- `app/main.py` - Imported recurring payment models
- `app/api/routes.py` - Registered recurring payments router
- `app/api/v1/intelligence_pages.py` - New bills-subscriptions route, redirects
- `app/services/calendar_service.py` - Integrated bills into calendar
- `app/templates/intelligence/dashboard.html` - Updated bills card, dark theme
- `app/templates/intelligence/budget_recommendations.html` - Dark theme fixes
- `app/templates/intelligence/duplicates.html` - Dark theme fixes

## API Documentation

### Create Recurring Payment
```http
POST /api/v1/recurring-payments/
Content-Type: application/json

{
  "category_id": 5,
  "name": "Netflix Subscription",
  "description": "Family plan",
  "amount": 15.99,
  "currency_code": "USD",
  "frequency": "MONTHLY",
  "due_day": 15,
  "start_date": "2025-01-01",
  "remind_days_before": 3
}

Response 200:
{
  "id": 1,
  "name": "Netflix Subscription",
  "amount": 15.99,
  "currency_code": "USD",
  "frequency": "monthly",
  "due_day": 15,
  "category_id": 5,
  "category_name": "Entertainment",
  "next_due_date": "2025-02-15",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00"
}
```

### Get All Payments
```http
GET /api/v1/recurring-payments/?include_inactive=false

Response 200:
{
  "payments": [
    {
      "id": 1,
      "name": "Netflix",
      "amount": 15.99,
      "frequency": "monthly",
      "next_due_date": "2025-02-15",
      "days_until_due": 10,
      "is_active": true
    }
  ],
  "count": 1
}
```

### Get Payment Summary
```http
GET /api/v1/recurring-payments/summary

Response 200:
{
  "total_payments": 5,
  "active_payments": 4,
  "inactive_payments": 1,
  "total_monthly_cost": 125.50,
  "total_annual_cost": 1506.00,
  "upcoming_payments": [
    {
      "name": "Netflix",
      "amount": 15.99,
      "due_date": "2025-02-15",
      "days_until_due": 10
    }
  ]
}
```

### Get Active Reminders
```http
GET /api/v1/recurring-payments/reminders/active?days_ahead=14

Response 200:
{
  "reminders": [
    {
      "id": 1,
      "payment_name": "Netflix",
      "amount": 15.99,
      "due_date": "2025-02-15",
      "days_until_due": 10,
      "is_dismissed": false,
      "is_paid": false
    }
  ],
  "count": 1
}
```

## Conclusion

Phase 28 successfully transforms the bills and subscriptions system from an unreliable AI-detected approach to a robust user-managed system. This gives users full control over what is considered a recurring payment while leveraging AI only for helpful reminders.

The unified interface streamlines bill management, the calendar integration provides visual planning aids, and the dark theme fixes ensure consistency across all intelligence features.

Key achievements:
- ✅ User-managed recurring payment system
- ✅ Flexible frequency support (weekly to annually)
- ✅ AI warnings without auto-detection
- ✅ Calendar integration with bill visualization
- ✅ Consistent dark theme across intelligence pages
- ✅ Seamless category management integration
- ✅ Complete REST API with validation
- ✅ Backward compatible route redirects

This implementation provides a solid foundation for future enhancements like payment history tracking, auto-linking with entries, and advanced analytics.
