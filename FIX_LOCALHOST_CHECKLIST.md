# Fix Localhost Issues - Quick Checklist

## Issues to Fix:
1. ❌ Migration version mismatch (orphaned migration in local DB)
2. ❌ Gmail SMTP authentication failing (needs App Password)

---

## ✅ Step-by-Step Instructions

### 1. Stop the Server
```bash
# Press Ctrl+C in the terminal where the server is running
```

### 2. Delete Old Database

**Option A - Use the batch script:**
```bash
# Double-click this file:
fix_local_db.bat
```

**Option B - Manual deletion:**
```bash
# In the project directory, delete app.db
# Windows Explorer: Find app.db and delete it
# Or command line:
del app.db
```

### 3. Set Up Gmail App Password

📖 **Follow the detailed guide:** [GMAIL_SETUP_GUIDE.md](GMAIL_SETUP_GUIDE.md)

**Quick steps:**
1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification" (if not already enabled)
3. Go to https://myaccount.google.com/apppasswords
4. Select app: "Mail", device: "Other (Budget Pulse)"
5. Click "Generate"
6. Copy the 16-character password (remove spaces)
7. Update your `.env` file:
   ```env
   SMTP_USERNAME=info@yourbudgetpulse.online
   SMTP_PASSWORD=your16charpassword
   FROM_EMAIL=info@yourbudgetpulse.online
   ```

### 4. Verify Your .env File

Open `.env` and make sure you have:
```env
# Database (will be created automatically)
DATABASE_URL=sqlite:///./app.db
ENV=dev

# Email Configuration
SMTP_USERNAME=info@yourbudgetpulse.online
SMTP_PASSWORD=abcdefghijklmnop  # Your 16-char App Password (no spaces!)
FROM_EMAIL=info@yourbudgetpulse.online

# App Settings
SECRET_KEY=your-secret-key-here
BASE_URL=http://localhost:8000
```

### 5. Start the Server
```bash
python run_local.py
```

### 6. Test Registration

1. Open http://localhost:8000
2. Click "Sign Up"
3. Register a new user
4. Watch the terminal for:
   ```
   ✅ Email sent successfully via SMTP
   ✅ Confirmation email sent to user@example.com
   ```
5. Check your email inbox for the verification email

---

## ✅ Success Indicators

You should see these messages in the terminal:

```
✅ Database tables created/verified
✅ User created successfully
✅ Email sent successfully via SMTP
✅ Confirmation email sent to [email]
```

## ❌ If You Still Have Issues

### Issue: Can't delete app.db (file locked)
**Solution**: Make sure all Python processes are stopped
```bash
# Windows: Open Task Manager → End all python.exe processes
# Or run:
taskkill /F /IM python.exe
```

### Issue: SMTP still failing after App Password setup
**Checklist**:
- [ ] 2-Step Verification is enabled on Gmail
- [ ] You waited 5-10 minutes after enabling 2-Step Verification
- [ ] App Password has NO spaces (should be 16 characters with no spaces)
- [ ] SMTP_USERNAME matches the Gmail account that generated the App Password
- [ ] You're using the App Password, not your regular Gmail password
- [ ] You saved the `.env` file after making changes
- [ ] You restarted the server after updating `.env`

### Issue: Migration errors
**Solution**: Make sure app.db was deleted before starting the server
```bash
# Check if app.db exists:
dir app.db

# If it exists, force delete:
del /F app.db
```

---

## Alternative: Use Resend API Instead

If Gmail setup is too complicated:

1. Sign up at https://resend.com (free tier)
2. Get your API key
3. Update `.env`:
   ```env
   RESEND_API_KEY=re_xxxxxxxxxxxxx

   # Comment out Gmail SMTP settings:
   # SMTP_USERNAME=info@yourbudgetpulse.online
   # SMTP_PASSWORD=abcdefghijklmnop
   # FROM_EMAIL=info@yourbudgetpulse.online
   ```
4. Restart server

---

## Need Help?

- Gmail setup details: [GMAIL_SETUP_GUIDE.md](GMAIL_SETUP_GUIDE.md)
- Full documentation: [README.md](README.md)
- Testing guide: [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

**Last Updated**: November 11, 2025
