# Budget Pulse API Documentation

**Version:** 1.0  
**Base URL:** `https://yourbudgetpulse.online` (Production) or `http://localhost:8000` (Development)  
**Authentication:** Session-based authentication with secure cookies

---

## Table of Contents

1. [Authentication](#authentication)
2. [Entries (Transactions)](#entries)
3. [Categories](#categories)
4. [Dashboard](#dashboard)
5. [Metrics & Charts](#metrics--charts)
6. [AI Features](#ai-features)
7. [Reports](#reports)
8. [Currency](#currency)
9. [Error Codes](#error-codes)

---

## Authentication

### Register User
**Endpoint:** `POST /auth/register`  
**Auth Required:** No  
**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**
- `email` (string, required): User's email address
- `password` (string, required): Password (min 8 characters)
- `full_name` (string, optional): User's full name

**Success Response (302):**
- Redirects to `/auth/verification-sent`
- Sends verification email to user

**Error Responses:**
- `400 Bad Request`: Invalid email or weak password
- `409 Conflict`: Email already registered

**Example:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -d "email=user@example.com" \
  -d "password=SecurePass123!" \
  -d "full_name=John Doe"
```

---

### Login
**Endpoint:** `POST /auth/login`  
**Auth Required:** No  
**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**
- `email` (string, required): User's email
- `password` (string, required): User's password

**Success Response (302):**
- Redirects to `/` (dashboard)
- Sets `session_id` cookie (secure, httponly)

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Email not verified

**Example:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -d "email=user@example.com" \
  -d "password=SecurePass123!" \
  -c cookies.txt
```

---

### Logout
**Endpoint:** `POST /auth/logout`  
**Auth Required:** Yes  

**Success Response (302):**
- Redirects to `/auth/login`
- Clears session cookie

---

### Forgot Password
**Endpoint:** `POST /auth/forgot-password`  
**Auth Required:** No  
**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**
- `email` (string, required): User's email

**Success Response (302):**
- Sends password reset email
- Redirects to confirmation page

---

## Entries

### List Entries
**Endpoint:** `GET /entries/`  
**Auth Required:** Yes  
**Response:** HTML page

**Query Parameters:**
- `start` (date, optional): Start date filter (ISO format: YYYY-MM-DD)
- `end` (date, optional): End date filter (ISO format: YYYY-MM-DD)
- `category` (string, optional): Category ID or "all"

**Example:**
```bash
curl -X GET "http://localhost:8000/entries/?start=2025-01-01&end=2025-01-31&category=5" \
  -b cookies.txt
```

---

### Create Entry
**Endpoint:** `POST /entries/create`  
**Auth Required:** Yes  
**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**
- `type` (string, required): "income" or "expense"
- `amount` (float, required): Transaction amount (positive number)
- `category_id` (integer, optional): Category ID
- `note` (string, optional): Transaction description
- `date` (date, required): Transaction date (ISO format)

**Success Response (200):**
- Returns updated entry list HTML fragment
- Triggers report status update to "New"
- May trigger AI category suggestion

**Error Responses:**
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Not authenticated

**Example:**
```bash
curl -X POST http://localhost:8000/entries/create \
  -b cookies.txt \
  -d "type=expense" \
  -d "amount=50.00" \
  -d "category_id=3" \
  -d "note=Grocery shopping" \
  -d "date=2025-01-15"
```

---

### Update Entry Amount
**Endpoint:** `POST /entries/update/{entry_id}/amount`  
**Auth Required:** Yes  

**Parameters:**
- `entry_id` (integer, path): Entry ID to update
- `amount` (float, form): New amount

**Success Response (200):**
- Returns updated entry HTML fragment

---

### Delete Entry
**Endpoint:** `POST /entries/delete/{entry_id}`  
**Auth Required:** Yes  

**Parameters:**
- `entry_id` (integer, path): Entry ID to delete

**Success Response (200):**
- Returns updated entry list HTML fragment

---

## Categories

### List Categories
**Endpoint:** `GET /categories/`  
**Auth Required:** Yes  
**Response:** HTML page with user's categories

---

### Create Category
**Endpoint:** `POST /categories/create`  
**Auth Required:** Yes  

**Parameters:**
- `name` (string, required): Category name (unique per user)

**Success Response (200):**
- Returns updated category list HTML fragment

**Error Responses:**
- `400 Bad Request`: Category name already exists

---

### Edit Category
**Endpoint:** `POST /categories/edit/{category_id}`  
**Auth Required:** Yes  

**Parameters:**
- `category_id` (integer, path): Category ID
- `name` (string, required): New category name

**Success Response (200):**
- Returns updated category HTML fragment

---

### Delete Category
**Endpoint:** `POST /categories/delete/{category_id}`  
**Auth Required:** Yes  

**Parameters:**
- `category_id` (integer, path): Category ID to delete

**Success Response (200):**
- Returns updated category list HTML fragment
- Entries with this category become uncategorized

---

## Dashboard

### View Dashboard
**Endpoint:** `GET /`  
**Auth Required:** Yes  
**Response:** HTML page with dashboard

**Query Parameters:**
- `start` (date, optional): Start date for metrics
- `end` (date, optional): End date for metrics
- `category` (string, optional): Category filter

---

### Summary Panel (HTMX)
**Endpoint:** `GET /dashboard/summary`  
**Auth Required:** Yes  
**Response:** HTML fragment

**Query Parameters:**
- `start` (date, optional)
- `end` (date, optional)
- `category` (string, optional)

**Returns:** Summary cards with income, expenses, and balance

---

### Expenses Panel (HTMX)
**Endpoint:** `GET /dashboard/expenses`  
**Auth Required:** Yes  
**Response:** HTML fragment

**Returns:** Table of recent expenses

---

### Incomes Panel (HTMX)
**Endpoint:** `GET /dashboard/incomes`  
**Auth Required:** Yes  
**Response:** HTML fragment

**Returns:** Table of recent income entries

---

## Metrics & Charts

### Daily Expenses Chart
**Endpoint:** `GET /metrics/chart/daily`  
**Auth Required:** Yes  
**Response:** HTML fragment with Chart.js

**Query Parameters:**
- `start` (date, optional)
- `end` (date, optional)

**Returns:** Line chart showing daily expense trends

---

### Category Bar Chart
**Endpoint:** `GET /metrics/chart/bar`  
**Auth Required:** Yes  
**Response:** HTML fragment with Chart.js

**Returns:** Bar chart of expenses by category

---

### Category Pie Chart
**Endpoint:** `GET /metrics/chart/pie`  
**Auth Required:** Yes  
**Response:** HTML fragment with Chart.js

**Returns:** Pie chart of expense distribution

---

## AI Features

### Get AI Settings
**Endpoint:** `GET /ai/settings`  
**Auth Required:** Yes  
**Response:** HTML page

**Returns:** AI configuration page with model status

---

### Update AI Settings
**Endpoint:** `POST /ai/settings`  
**Auth Required:** Yes  

**Parameters:**
- `auto_categorization` (boolean): Enable/disable auto-categorization
- `show_confidence` (boolean): Show confidence scores
- `min_confidence` (float): Minimum confidence threshold (0.0-1.0)
- `learning_enabled` (boolean): Enable learning from feedback

**Success Response (302):**
- Redirects to `/ai/settings`
- Updates user AI preferences

---

### Get Model Status
**Endpoint:** `GET /ai/model/status`  
**Auth Required:** Yes  
**Response:** JSON

**Success Response (200):**
```json
{
  "is_trained": true,
  "accuracy": 0.85,
  "trained_on": 150,
  "last_trained": "2025-01-15T10:30:00",
  "total_predictions": 45,
  "accepted_predictions": 38
}
```

---

### Train AI Model
**Endpoint:** `POST /ai/model/train`  
**Auth Required:** Yes  
**Response:** JSON

**Success Response (200):**
```json
{
  "success": true,
  "accuracy": 0.85,
  "trained_on": 150,
  "message": "Model trained successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Insufficient training data
```json
{
  "success": false,
  "error": "Not enough data to train model. Need at least 30 entries."
}
```

---

### Retrain AI Model
**Endpoint:** `POST /ai/model/retrain`  
**Auth Required:** Yes  
**Response:** JSON

**Success Response (200):**
```json
{
  "success": true,
  "accuracy": 0.87,
  "trained_on": 200,
  "message": "Model retrained successfully"
}
```

---

### Get Category Suggestion
**Endpoint:** `POST /ai/suggest-category`  
**Auth Required:** Yes  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "note": "Whole Foods grocery shopping",
  "amount": 45.50,
  "type": "expense",
  "date": "2025-01-15"
}
```

**Success Response (200):**
```json
{
  "category_id": 7,
  "category_name": "Groceries",
  "confidence_score": 0.85,
  "reasoning": "ML model prediction"
}
```

**Response when no suggestion (200):**
```json
{
  "category_id": null,
  "confidence_score": 0.0,
  "reasoning": "Model not trained or low confidence"
}
```

---

### Record AI Feedback
**Endpoint:** `POST /ai/feedback`  
**Auth Required:** Yes  

**Parameters:**
- `suggestion_id` (integer): AI suggestion ID
- `accepted` (boolean): Whether user accepted suggestion

**Success Response (200):**
```json
{
  "success": true,
  "message": "Feedback recorded"
}
```

---

## Reports

### Reports Main Page
**Endpoint:** `GET /reports/`  
**Auth Required:** Yes  
**Response:** HTML page

**Returns:** Financial reports hub with links to weekly, monthly, annual reports

---

### Weekly Report
**Endpoint:** `GET /reports/weekly`  
**Auth Required:** Yes  
**Response:** HTML page

**Returns:** Comprehensive weekly financial report including:
- Summary metrics (expenses, income, net, transactions)
- Week-over-week comparison
- Key insights
- Achievements
- Recommendations
- Anomaly detection
- Daily breakdown

---

### Monthly Report
**Endpoint:** `GET /reports/monthly`  
**Auth Required:** Yes  
**Response:** HTML page

**Returns:** Monthly financial report including:
- Monthly summary
- Category analysis
- Spending trends
- Month-over-month comparison
- Insights and recommendations

---

### Annual Report
**Endpoint:** `GET /reports/annual`  
**Auth Required:** Yes  
**Response:** HTML page

**Returns:** Annual financial summary

---

### Email Weekly Report
**Endpoint:** `POST /reports/weekly/email`  
**Auth Required:** Yes  
**Response:** JSON

**Success Response (200):**
```json
{
  "success": true,
  "message": "Weekly report email sent successfully"
}
```

---

### Email Monthly Report
**Endpoint:** `POST /reports/monthly/email`  
**Auth Required:** Yes  
**Response:** JSON

**Success Response (200):**
```json
{
  "success": true,
  "message": "Monthly report email sent successfully"
}
```

---

### Email Annual Report
**Endpoint:** `POST /reports/annual/email`  
**Auth Required:** Yes  
**Response:** JSON

**Success Response (200):**
```json
{
  "success": true,
  "message": "Annual report email sent successfully"
}
```

---

### Get Report Statuses
**Endpoint:** `GET /reports/status/`  
**Auth Required:** Yes  
**Response:** JSON

**Success Response (200):**
```json
{
  "statuses": {
    "weekly": {
      "is_new": true,
      "last_viewed": "2025-01-15T10:30:00",
      "last_updated": "2025-01-16T08:00:00"
    },
    "monthly": {
      "is_new": false,
      "last_viewed": "2025-01-16T09:00:00",
      "last_updated": "2025-01-16T08:00:00"
    },
    "annual": {
      "is_new": true,
      "last_viewed": null,
      "last_updated": "2025-01-16T08:00:00"
    }
  }
}
```

---

### Mark Report as Viewed
**Endpoint:** `POST /reports/status/mark-viewed`  
**Auth Required:** Yes  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "report_type": "weekly",
  "report_period": "current"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "weekly report marked as viewed"
}
```

---

### Export to Excel
**Endpoint:** `GET /reports/export/excel`  
**Auth Required:** Yes  
**Response:** File download (`.xlsx`)

**Query Parameters:**
- `start` (date, required): Start date (YYYY-MM-DD)
- `end` (date, required): End date (YYYY-MM-DD)
- `category` (string, optional): Category ID or "all"

**Success Response (200):**
- Downloads Excel file with detailed transaction list

---

### Export to PDF
**Endpoint:** `GET /reports/export/pdf`  
**Auth Required:** Yes  
**Response:** File download (`.pdf`)

**Query Parameters:**
- `start` (date, required)
- `end` (date, required)
- `category` (string, optional)

**Success Response (200):**
- Downloads PDF file with charts and summary

---

### Category Summary Export
**Endpoint:** `GET /reports/export/category-summary`  
**Auth Required:** Yes  
**Response:** File download (`.xlsx`)

**Query Parameters:**
- `start` (date, required)
- `end` (date, required)
- `category` (string, optional)

**Success Response (200):**
- Downloads Excel file with category breakdown

---

## Currency

### Get Currency Settings
**Endpoint:** `GET /currency/settings`  
**Auth Required:** Yes  
**Response:** HTML page

**Returns:** Currency selection page with current preference

---

### Update Currency
**Endpoint:** `POST /currency/update`  
**Auth Required:** Yes  

**Parameters:**
- `currency_code` (string, required): ISO 4217 currency code (e.g., "USD", "EUR", "TRY")

**Success Response (302):**
- Updates user currency preference
- Redirects to dashboard or previous page

**Supported Currencies:**
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- TRY (Turkish Lira)
- JPY (Japanese Yen)
- CAD (Canadian Dollar)
- AUD (Australian Dollar)
- CHF (Swiss Franc)
- CNY (Chinese Yuan)
- INR (Indian Rupee)

---

## Error Codes

### Standard HTTP Status Codes

**2xx Success:**
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `302 Found`: Redirect

**4xx Client Errors:**
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied (e.g., unverified email)
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate email)
- `422 Unprocessable Entity`: Validation error

**5xx Server Errors:**
- `500 Internal Server Error`: Server error occurred

---

## Response Formats

### HTML Responses
Most endpoints return HTML (full pages or fragments for HTMX)

### JSON Responses
AI and API endpoints return JSON:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error description",
  "message": "User-friendly message"
}
```

---

## Rate Limiting

**Current Limits:**
- None implemented (recommend implementing in production)

**Recommended Future Limits:**
- API requests: 100 per minute per user
- AI predictions: 50 per minute per user
- Report generation: 10 per minute per user
- Email sending: 5 per hour per user

---

## Authentication Details

### Session Cookie
- **Name:** `session_id`
- **Type:** Secure, HttpOnly
- **Duration:** 30 days
- **Storage:** Server-side session storage

### Protected Endpoints
All endpoints except `/auth/*` require authentication via session cookie.

---

## Webhooks (Future Feature)

**Planned webhooks for:**
- Transaction created
- Category assigned
- Report generated
- AI model trained
- Anomaly detected

---

## Versioning

**Current Version:** v1  
**API Prefix:** `/api/v1/*` (not currently used, direct routes used)  
**Backward Compatibility:** Maintained for all v1 endpoints

---

## Best Practices

### Making Requests

1. **Always include authentication:**
```bash
curl -b cookies.txt http://localhost:8000/endpoint
```

2. **Use proper content types:**
```bash
# Form data
-H "Content-Type: application/x-www-form-urlencoded"

# JSON data
-H "Content-Type: application/json"
```

3. **Handle redirects:**
```bash
curl -L http://localhost:8000/endpoint  # Follow redirects
```

4. **Check response status:**
Always check HTTP status codes before processing response

---

## Support

**Issues:** https://github.com/TurtleWithGlasses/expense-manager-web-app/issues  
**Email:** support@yourbudgetpulse.online  
**Documentation:** This file and TECHNICAL_ARCHITECTURE.md

---

**Last Updated:** January 2025  
**Maintained by:** Budget Pulse Development Team

