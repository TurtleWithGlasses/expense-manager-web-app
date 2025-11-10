#!/usr/bin/env python
"""
Test Email Configuration
Verifies that SMTP credentials are working correctly
"""
import os
import sys
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

def test_smtp_connection():
    """Test SMTP connection with current .env settings"""

    print("=" * 50)
    print("Testing Email Configuration")
    print("=" * 50)
    print()

    # Get credentials from environment
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL")

    # Check if credentials exist
    print("📋 Configuration Check:")
    print(f"   SMTP_USERNAME: {'✅ Set' if username else '❌ Not set'}")
    print(f"   SMTP_PASSWORD: {'✅ Set' if password else '❌ Not set'} ({len(password) if password else 0} characters)")
    print(f"   FROM_EMAIL: {'✅ Set' if from_email else '❌ Not set'}")
    print()

    if not username or not password:
        print("❌ Missing SMTP credentials in .env file")
        print()
        print("Please add these to your .env file:")
        print("   SMTP_USERNAME=your-email@gmail.com")
        print("   SMTP_PASSWORD=your16charapppassword")
        print("   FROM_EMAIL=your-email@gmail.com")
        print()
        print("📖 See GMAIL_SETUP_GUIDE.md for detailed instructions")
        return False

    # Test connection
    print("🔌 Testing SMTP connection...")
    print(f"   Server: smtp.gmail.com:587")
    print(f"   Username: {username}")
    print()

    try:
        # Connect to Gmail SMTP
        print("1️⃣ Connecting to SMTP server...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        print("   ✅ Connected")

        print("2️⃣ Starting TLS encryption...")
        server.starttls()
        print("   ✅ TLS enabled")

        print("3️⃣ Authenticating...")
        server.login(username, password)
        print("   ✅ Authentication successful!")

        print("4️⃣ Closing connection...")
        server.quit()
        print("   ✅ Connection closed")

        print()
        print("=" * 50)
        print("✅ SUCCESS! Email configuration is working!")
        print("=" * 50)
        print()
        print("You can now:")
        print("1. Start the server: python run_local.py")
        print("2. Register a new user")
        print("3. Email will be sent successfully")
        print()
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Authentication failed: {e}")
        print()
        print("=" * 50)
        print("❌ SMTP Authentication Error")
        print("=" * 50)
        print()
        print("Possible causes:")
        print("1. You're using your regular Gmail password instead of an App Password")
        print("2. App Password has spaces (remove all spaces)")
        print("3. 2-Step Verification is not enabled on your Google account")
        print("4. The App Password was revoked or deleted")
        print()
        print("Solutions:")
        print("1. Enable 2-Step Verification: https://myaccount.google.com/security")
        print("2. Create new App Password: https://myaccount.google.com/apppasswords")
        print("3. Update SMTP_PASSWORD in .env (remove spaces!)")
        print("4. See GMAIL_SETUP_GUIDE.md for detailed instructions")
        print()
        return False

    except smtplib.SMTPException as e:
        print(f"   ❌ SMTP error: {e}")
        print()
        print("=" * 50)
        print("❌ SMTP Connection Error")
        print("=" * 50)
        print()
        print("Possible causes:")
        print("1. Network/firewall blocking SMTP port 587")
        print("2. Gmail server temporarily unavailable")
        print("3. Invalid SMTP credentials")
        print()
        return False

    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        print()
        return False

if __name__ == "__main__":
    success = test_smtp_connection()
    sys.exit(0 if success else 1)
