# Auto-Add to Expenses - Testing Guide

This guide explains how to test and verify the auto-add to expenses functionality for recurring bills and subscriptions.

## Overview

The auto-add feature automatically creates expense entries when recurring payments become due. The scheduled job runs daily at 1:00 AM, but we've added testing tools so you don't have to wait.

## Testing Methods

### Method 1: Manual Test Endpoint (Recommended)

Use the dedicated test endpoint to manually trigger the auto-add process:

**Endpoint:** `POST /api/v1/recurring-payments/test/process-auto-add`

**How to use:**
1. Make sure you're logged in
2. Send a POST request to the endpoint (you can use the browser console or a tool like Postman)
3. The endpoint will return detailed results

**Browser Console Example:**
```javascript
// Run this in your browser console while logged into the app
fetch('/api/v1/recurring-payments/test/process-auto-add', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    }
})
.then(r => r.json())
.then(data => console.log(data));
```

**Example Response:**
```json
{
    "today": "2025-12-29",
    "total_auto_add_enabled": 3,
    "processed": [
        {
            "id": 1,
            "name": "Netflix",
            "amount": 15.99,
            "currency": "USD",
            "frequency": "monthly",
            "due_day": 29,
            "is_due_today": true,
            "action": "created",
            "entry_id": 456,
            "description": "Netflix (Auto-added)"
        }
    ],
    "skipped": [
        {
            "id": 2,
            "name": "Spotify",
            "amount": 9.99,
            "currency": "USD",
            "frequency": "monthly",
            "due_day": 15,
            "is_due_today": false,
            "action": "not_due_today",
            "reason": "Payment not due today (due_day: 15, frequency: monthly)"
        }
    ],
    "errors": [],
    "summary": {
        "created": 1,
        "skipped": 1,
        "errors": 0
    }
}
```

### Method 2: Create a Test Payment

Create a recurring payment with today as the due date:

1. Go to **Bills & Subscriptions** page
2. Click **Add New Payment**
3. Fill in the details:
   - **Name:** Test Payment
   - **Category:** Any category
   - **Amount:** 10.00
   - **Frequency:** Monthly
   - **Due Day:** Today's day of month (e.g., if today is Dec 29, enter 29)
   - **Start Date:** Today or earlier
   - **✓ Check "Automatically add to expenses on due date"**
4. Save the payment
5. Use Method 1 to trigger the test endpoint
6. Check your **Entries** page to verify the expense was created

### Method 3: Check Scheduled Job Logs

The scheduled job runs automatically at 1:00 AM and prints detailed logs:

**Log Format:**
```
💰 Processing recurring payments at 2025-12-29 01:00:00
📋 Found 5 payments with auto-add enabled
✅ Auto-added expense for 'Netflix' - USD 15.99
⏭️  Skipping 'Spotify' - already added today
✅ Recurring payments processing completed
```

**Where to find logs:**
- **Local Development:** Terminal/console where uvicorn is running
- **Railway Production:** Railway logs dashboard

## What to Verify

### ✅ Checklist

- [ ] **Checkbox appears in UI** - Add/Edit payment modals show the auto-add checkbox
- [ ] **Checkbox value saved** - Creating/editing payment saves the checkbox state
- [ ] **API accepts field** - POST/PUT requests accept `auto_add_to_expenses` boolean
- [ ] **Due date detection works** - Payments due today are correctly identified
- [ ] **Expense entries created** - Expense entries are created with correct:
  - Category
  - Amount
  - Currency
  - Date (today)
  - Description (includes payment name + "Auto-added")
  - Type (expense)
- [ ] **No duplicates** - Running the job multiple times doesn't create duplicate entries
- [ ] **All frequencies work** - Test with different frequencies:
  - Weekly (due_day = day of week, 0-6)
  - Biweekly (due_day = day of week, checks 2-week intervals)
  - Monthly (due_day = day of month, 1-31)
  - Quarterly (due_day = day of month, runs on months 1, 4, 7, 10)
  - Annually (due_day = day of month, matches start_date month)

## Troubleshooting

### Problem: Test endpoint returns empty results

**Solution:** Create a payment with auto-add enabled and due today
```json
{
    "total_auto_add_enabled": 0,
    "processed": [],
    "skipped": []
}
```

### Problem: Payment not processing even though it's the due date

**Possible causes:**
1. **Payment is inactive** - Check `is_active` field
2. **Auto-add disabled** - Check `auto_add_to_expenses` field
3. **Payment ended** - Check `end_date` hasn't passed
4. **Start date in future** - Check `start_date` is today or earlier
5. **Wrong due_day calculation** - Verify due_day logic for the frequency

**Debug with test endpoint:** The response shows `is_due_today: false` and the reason

### Problem: Duplicate entries created

**This should NOT happen** - The system checks for duplicates using:
- Same user
- Same category
- Same date (today)
- Same amount
- Same description (contains payment name)

**If duplicates occur:**
1. Check database for duplicate detection query
2. Verify the `description` field includes payment name
3. Check scheduled job logs for errors

## Frequency Due Date Logic

### Weekly
- `due_day` = day of week (0 = Monday, 6 = Sunday)
- Example: `due_day: 1` = Every Tuesday

### Biweekly
- `due_day` = day of week (0-6)
- Checks it's been 2 weeks since `start_date`
- Example: `due_day: 3, start_date: 2025-01-01` = Every other Wednesday starting Jan 1

### Monthly
- `due_day` = day of month (1-31)
- Example: `due_day: 15` = 15th of every month

### Quarterly
- `due_day` = day of month (1-31)
- Only processes on months 1, 4, 7, 10
- Example: `due_day: 1` = Jan 1, Apr 1, Jul 1, Oct 1

### Annually
- `due_day` = day of month (1-31)
- Month comes from `start_date`
- Example: `start_date: 2025-03-15, due_day: 15` = March 15 every year

## Production Testing

Once deployed to Railway:

1. **Check deployment logs** - Verify the scheduler started:
   ```
   📅 Report scheduler started successfully
   ```

2. **Create test payment** - Use production UI to create a test payment

3. **Wait for 1:00 AM** - Or manually trigger via test endpoint

4. **Check Railway logs** - Look for auto-add processing logs

5. **Verify in UI** - Check Entries page for auto-added expenses

## API Endpoints Reference

### Create Payment with Auto-Add
```bash
POST /api/v1/recurring-payments/
Content-Type: application/json

{
    "name": "Netflix",
    "category_id": 1,
    "amount": 15.99,
    "frequency": "MONTHLY",
    "due_day": 29,
    "start_date": "2025-12-01",
    "auto_add_to_expenses": true
}
```

### Update Auto-Add Setting
```bash
PUT /api/v1/recurring-payments/{payment_id}
Content-Type: application/json

{
    "auto_add_to_expenses": true
}
```

### Test Auto-Add Process
```bash
POST /api/v1/recurring-payments/test/process-auto-add
```

### Get Payment Summary
```bash
GET /api/v1/recurring-payments/summary
```

## Next Steps

After verifying the feature works:

1. **Monitor for 24 hours** - Ensure scheduled job runs at 1 AM
2. **Check all frequency types** - Test weekly, monthly, quarterly, etc.
3. **Verify no duplicates** - Run job multiple times on same day
4. **Test edge cases:**
   - Payments that start in the future
   - Payments that have ended
   - Inactive payments
   - Different currencies

## Notes

- The test endpoint only processes the **current user's** payments
- The scheduled job processes **all users'** payments
- Auto-added entries have "(Auto-added)" suffix in description
- Duplicate prevention is very strict to avoid double-charging
