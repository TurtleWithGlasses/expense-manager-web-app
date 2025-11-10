# Gmail SMTP Setup Guide

This guide will help you set up Gmail SMTP for sending emails from the Budget Pulse application.

## Problem

Gmail blocks regular password login for third-party applications for security reasons. You need to use an "App Password" instead.

Error you're seeing:
```
❌ SMTP error: (534, b'5.7.9 Please log in with your web browser and then try again...')
```

## Solution: Create Gmail App Password

### Step 1: Enable 2-Step Verification

1. Go to your Google Account: https://myaccount.google.com/security
2. Under "How you sign in to Google", click on **"2-Step Verification"**
3. If not enabled:
   - Click **"Get Started"**
   - Follow the prompts to set up 2-Step Verification
   - You'll need to verify your phone number
   - Complete the setup

### Step 2: Create App Password

1. Go to App Passwords page: https://myaccount.google.com/apppasswords
   - (Or: Google Account → Security → 2-Step Verification → scroll down to "App passwords")

2. You might need to sign in again

3. At the "App passwords" screen:
   - Under "Select app": Choose **"Mail"**
   - Under "Select device": Choose **"Other (Custom name)"**
   - Type: **"Budget Pulse"** or **"Expense Manager"**
   - Click **"Generate"**

4. Google will show you a 16-character password like this:
   ```
   abcd efgh ijkl mnop
   ```

5. **IMPORTANT**: Copy this password immediately! You won't be able to see it again.

### Step 3: Update Your .env File

1. Open your `.env` file in the project root directory

2. Find the email configuration section (or add it):
   ```env
   # Email Configuration (Gmail SMTP)
   SMTP_USERNAME=info@yourbudgetpulse.online
   SMTP_PASSWORD=abcdefghijklmnop
   FROM_EMAIL=info@yourbudgetpulse.online
   ```

3. Replace `abcdefghijklmnop` with your actual 16-character app password
   - **Remove all spaces** from the password
   - Example: If Google gave you `abcd efgh ijkl mnop`, use `abcdefghijklmnop`

4. Save the `.env` file

### Step 4: Restart the Server

1. Stop the server if it's running (Ctrl+C in the terminal)
2. Start it again:
   ```bash
   python run_local.py
   ```

### Step 5: Test Email

1. Try registering a new user
2. You should see:
   ```
   ✅ Email sent successfully via SMTP
   ✅ Confirmation email sent to user@example.com
   ```

## Troubleshooting

### "App passwords" option not available

**Cause**: 2-Step Verification is not enabled

**Solution**:
- Go to https://myaccount.google.com/security
- Enable 2-Step Verification first
- Wait a few minutes, then try accessing App passwords again

### Still getting authentication errors

**Possible causes**:
1. You copied the password with spaces → Remove all spaces
2. You're using the wrong Google account → Make sure you're logged into `info@yourbudgetpulse.online`
3. 2-Step Verification was just enabled → Wait 5-10 minutes for Google to propagate the change

### Alternative: Use a different email account

If `info@yourbudgetpulse.online` is not a Gmail account, you need to:

**Option A**: Create a new Gmail account for sending emails
- Create: `budgetpulse.noreply@gmail.com`
- Enable 2-Step Verification
- Create App Password
- Update `.env` with the new credentials

**Option B**: Use Resend API instead (easier)
- Sign up at https://resend.com (free tier: 3,000 emails/month)
- Get API key
- Update `.env`:
  ```env
  RESEND_API_KEY=re_xxxxxxxxxxxxx
  # Comment out SMTP settings
  # SMTP_USERNAME=...
  # SMTP_PASSWORD=...
  ```

## Security Notes

- **Never commit your App Password to Git**
- `.env` file is already in `.gitignore`
- App Passwords only work for the specific app/device
- You can revoke App Passwords at any time from Google Account settings
- Each app should have its own unique App Password

## Questions?

If you have issues:
1. Check that 2-Step Verification is enabled
2. Make sure you're using the App Password, not your regular Google password
3. Verify there are no spaces in the password in `.env`
4. Check that `SMTP_USERNAME` matches the Gmail account that generated the App Password

---

**Last Updated**: November 11, 2025
