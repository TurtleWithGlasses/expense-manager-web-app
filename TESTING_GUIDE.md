# Production Testing Guide

**Production URL:** https://www.yourbudgetpulse.online
**Date:** November 9, 2025
**Version:** 1.0

---

## 🎯 Testing Objectives

- Verify all core features work in production
- Test AI/ML features with real data
- Validate multi-currency support
- Ensure reports generate correctly
- Check theme switching and preferences
- Verify security features (email verification, password reset)

---

## ✅ **Test 1: User Registration & Authentication** (5 minutes)

### **1.1 Register New User**
- [ ] Go to https://www.yourbudgetpulse.online
- [ ] Click "Register" or "Sign Up"
- [ ] Fill in:
  - Full Name: `Test User`
  - Email: `your-test-email@example.com`
  - Password: `TestPassword123!`
- [ ] Submit registration
- [ ] **Expected:** Success message, redirected to dashboard or email verification page

### **1.2 Email Verification**
- [ ] Check email inbox for verification email
- [ ] Click verification link
- [ ] **Expected:** Email verified successfully, can now log in

**If email doesn't arrive:**
- Check spam folder
- Email service might be rate-limited
- Check Railway logs for email sending errors

### **1.3 Login**
- [ ] Go to login page
- [ ] Enter email and password
- [ ] **Expected:** Redirected to dashboard

### **1.4 Password Reset (Optional)**
- [ ] Click "Forgot Password"
- [ ] Enter email address
- [ ] Check email for reset link
- [ ] Click link and set new password
- [ ] **Expected:** Password reset successful, can log in with new password

---

## ✅ **Test 2: Dashboard & Entry Management** (5 minutes)

### **2.1 View Dashboard**
- [ ] After login, view main dashboard
- [ ] **Expected:** See:
  - Summary cards (Total Income, Total Expenses, Net Savings)
  - Empty state or sample data message
  - Category breakdown chart (empty if no data)
  - Quick action buttons

### **2.2 Add Expense Entry**
- [ ] Click "Add Entry" or "+" button
- [ ] Fill in:
  - Type: `Expense`
  - Amount: `50.00`
  - Category: `Groceries` (or create new category)
  - Date: Today's date
  - Notes: `Weekly grocery shopping`
  - Currency: `USD`
- [ ] Submit
- [ ] **Expected:** Entry appears in entry list, dashboard updates

### **2.3 Add Income Entry**
- [ ] Click "Add Entry"
- [ ] Fill in:
  - Type: `Income`
  - Amount: `1000.00`
  - Category: `Salary` (or create new)
  - Date: Today's date
  - Notes: `Monthly salary`
  - Currency: `USD`
- [ ] Submit
- [ ] **Expected:** Entry appears, dashboard shows updated totals

### **2.4 Add More Entries**
Add at least 5-10 more entries with varied:
- [ ] Amounts ($10 - $500)
- [ ] Categories (Groceries, Transportation, Entertainment, Utilities, Dining)
- [ ] Dates (spread across current month)
- [ ] Types (mix of income and expenses)

**Expected:** Dashboard updates with each entry, charts populate

---

## ✅ **Test 3: Category Management** (3 minutes)

### **3.1 View Categories**
- [ ] Navigate to Categories page
- [ ] **Expected:** See list of categories with entry counts

### **3.2 Create Custom Category**
- [ ] Click "Add Category"
- [ ] Enter name: `Coffee`
- [ ] Submit
- [ ] **Expected:** Category appears in list

### **3.3 Edit Category**
- [ ] Click edit icon on a category
- [ ] Change name: `Coffee` → `Coffee & Snacks`
- [ ] Save
- [ ] **Expected:** Category name updated

### **3.4 Delete Category**
- [ ] Create a test category: `Test Category`
- [ ] Delete it
- [ ] **Expected:** Category removed, entries reassigned or orphaned

---

## ✅ **Test 4: AI Features** (5 minutes)

### **4.1 AI Category Suggestions**
- [ ] Add a new entry with description: `Coffee at Starbucks`
- [ ] **Expected:** AI suggests "Coffee" or "Dining" category with confidence score
- [ ] Accept or reject suggestion
- [ ] Add another: `Gas for car`
- [ ] **Expected:** AI suggests "Transportation" or "Auto"

### **4.2 AI Insights**
- [ ] Navigate to Insights page (if available in menu)
- [ ] **Expected:** See:
  - Spending patterns analysis
  - Top spending categories
  - Savings opportunities
  - Personalized recommendations
  - Spending trends

**Note:** May need 10+ entries for meaningful insights

### **4.3 Predictions**
- [ ] Look for "Predictions" section or page
- [ ] **Expected:** See:
  - Next month spending prediction
  - Category-wise forecasts
  - Confidence intervals
  - Trend analysis (increasing/decreasing/stable)

**Note:** May need 2-3 weeks of data for accurate predictions

### **4.4 Anomaly Detection**
- [ ] Add an unusually large expense: `Amount: $1000, Category: Groceries`
- [ ] Check Insights or Anomalies page
- [ ] **Expected:** System flags this as an anomaly with explanation

---

## ✅ **Test 5: Reports & Export** (5 minutes)

### **5.1 Weekly Report**
- [ ] Navigate to Reports page
- [ ] Select "Weekly Report"
- [ ] Choose date range (current week)
- [ ] **Expected:** See summary of weekly income/expenses

### **5.2 Excel Export**
- [ ] Click "Export to Excel" button
- [ ] **Expected:**
  - Excel file downloads
  - Open file: Contains entries with proper formatting
  - Includes charts and summaries

### **5.3 PDF Export**
- [ ] Click "Export to PDF" button
- [ ] **Expected:**
  - PDF file downloads
  - Open file: Contains entries, charts, and formatted report

### **5.4 Email Reports (if enabled)**
- [ ] Go to Settings → Report Preferences
- [ ] Enable weekly email reports
- [ ] Set frequency to "Weekly"
- [ ] Save preferences
- [ ] **Expected:** Settings saved, will receive email next week

---

## ✅ **Test 6: Multi-Currency** (3 minutes)

### **6.1 Change User Currency**
- [ ] Go to Settings → Currency
- [ ] Change default currency from USD to EUR (or any other)
- [ ] Save
- [ ] **Expected:** Dashboard amounts convert to EUR

### **6.2 Add Entry in Different Currency**
- [ ] Add entry with Amount: `100`, Currency: `GBP`
- [ ] **Expected:**
  - Entry saved in GBP
  - Dashboard shows converted amount in user's default currency

### **6.3 View Multi-Currency Summary**
- [ ] View dashboard with entries in multiple currencies
- [ ] **Expected:** Totals calculated correctly with conversions

---

## ✅ **Test 7: Goals** (5 minutes)

### **7.1 Create Savings Goal**
- [ ] Navigate to Goals page
- [ ] Click "Add Goal"
- [ ] Fill in:
  - Name: `Emergency Fund`
  - Type: `Savings Goal`
  - Target Amount: `5000`
  - Target Date: 3 months from now
  - Currency: `USD`
- [ ] Submit
- [ ] **Expected:** Goal appears with 0% progress

### **7.2 Log Progress**
- [ ] Click on the goal
- [ ] Add progress: `Amount: 500, Notes: Initial deposit`
- [ ] **Expected:** Progress bar updates to 10%

### **7.3 Create Spending Limit Goal**
- [ ] Add new goal:
  - Name: `Dining Budget`
  - Type: `Spending Limit`
  - Target Amount: `200`
  - Category: `Dining`
  - Target Date: End of current month
- [ ] **Expected:** Goal created, shows current spending vs limit

---

## ✅ **Test 8: Theme & Preferences** (2 minutes)

### **8.1 Toggle Theme**
- [ ] Click theme toggle button (moon/sun icon)
- [ ] **Expected:** Theme switches between dark and light mode
- [ ] Refresh page
- [ ] **Expected:** Theme preference persists

### **8.2 Update Display Preferences**
- [ ] Go to Settings → Appearance
- [ ] Change:
  - Compact mode: Toggle
  - Animations: Toggle
  - Font size: Change
- [ ] Save
- [ ] **Expected:** UI updates according to preferences

---

## ✅ **Test 9: Profile Management** (3 minutes)

### **9.1 Update Profile**
- [ ] Go to Settings → Profile
- [ ] Update full name
- [ ] **Expected:** Name updated, reflected in header/dashboard

### **9.2 Upload Avatar**
- [ ] Click "Upload Avatar"
- [ ] Select an image file (JPG/PNG, < 5MB)
- [ ] **Expected:**
  - Avatar preview shows
  - Avatar appears in header navigation
  - Page refresh persists avatar

### **9.3 Export Data**
- [ ] Click "Export Data" button
- [ ] **Expected:** JSON file downloads with all user data

---

## ✅ **Test 10: Security Features** (2 minutes)

### **10.1 Session Persistence**
- [ ] Close browser tab
- [ ] Reopen https://www.yourbudgetpulse.online
- [ ] **Expected:** Still logged in (session persists)

### **10.2 Logout**
- [ ] Click "Logout" button
- [ ] **Expected:** Redirected to login page
- [ ] Try accessing dashboard URL directly
- [ ] **Expected:** Redirected to login (protected route)

---

## 🐛 **Known Issues to Watch For**

### **Email Delivery**
- **Issue:** Emails might not send in production if SMTP is blocked
- **Workaround:** Check Railway logs, may need to use Resend API
- **Check:** Look for email sending errors in logs

### **AI Features**
- **Issue:** May need training data before suggestions appear
- **Workaround:** Add 10+ entries first, then test AI
- **Expected:** After ~20 entries, AI should start suggesting categories

### **Performance**
- **Issue:** First load might be slow (cold start)
- **Expected:** Subsequent loads should be fast
- **Check:** Page load time < 3 seconds after first visit

### **Migration Warnings**
- **Issue:** May see DuplicateColumn warning in logs on first startup
- **Expected:** Auto-stamps database, subsequent starts clean
- **Check:** Second deployment should show "[OK] Database already at latest migration"

---

## 📝 **Testing Results Template**

Use this template to record your findings:

```
# Production Testing Results
Date: [DATE]
Tester: [YOUR NAME]
Environment: Production (Railway)

## Test Results Summary
- [ ] User Registration & Auth: PASS / FAIL
- [ ] Dashboard & Entries: PASS / FAIL
- [ ] Categories: PASS / FAIL
- [ ] AI Features: PASS / FAIL
- [ ] Reports: PASS / FAIL
- [ ] Multi-Currency: PASS / FAIL
- [ ] Goals: PASS / FAIL
- [ ] Theme: PASS / FAIL
- [ ] Profile: PASS / FAIL
- [ ] Security: PASS / FAIL

## Issues Found
1. [Issue description]
   - Severity: Critical / High / Medium / Low
   - Steps to reproduce: [steps]
   - Expected: [expected behavior]
   - Actual: [actual behavior]

2. [Next issue...]

## Notes
[Any additional observations]
```

---

## 🚨 **Critical Issues to Report Immediately**

If you encounter any of these, report immediately:

1. **Cannot register or login** - Authentication broken
2. **Database errors** - Data not saving
3. **Application crashes** - Server errors (500)
4. **Security issues** - Unauthorized access, data leaks
5. **Payment/billing issues** - If applicable

---

## ✅ **Success Criteria**

Production is considered stable if:
- [x] Users can register and login
- [x] Entries can be created, edited, deleted
- [x] Dashboard displays correct totals
- [x] Reports generate successfully
- [x] AI features provide suggestions (after training data)
- [x] Theme switching works
- [x] No critical errors in logs
- [x] Page load time < 5 seconds
- [x] Mobile responsive (test on phone)

---

## 📞 **Support**

If you encounter issues:
- Check Railway deployment logs
- Check browser console for JavaScript errors
- Check Network tab for failed API requests
- Report issues with screenshots and steps to reproduce

---

**Happy Testing! 🎉**
