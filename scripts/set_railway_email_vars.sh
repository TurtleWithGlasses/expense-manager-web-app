#!/usr/bin/env bash
# ============================================================
# Set email environment variables in Railway
# Usage:
#   1. railway login          (one-time, opens browser)
#   2. bash scripts/set_railway_email_vars.sh
# ============================================================

set -euo pipefail

echo "Setting email environment variables in Railway..."

# ---------- SMTP (Gmail App Password) ----------
railway variables set SMTP_SERVER=smtp.gmail.com
railway variables set SMTP_PORT=587
railway variables set SMTP_USERNAME=mhmtsoylu1928@gmail.com
railway variables set SMTP_PASSWORD="gglz dsci uhux qebl"
railway variables set FROM_EMAIL=mhmtsoylu1928@gmail.com
railway variables set FROM_NAME="Budget Pulse"

# ---------- SMTP fallback (SSL) ----------
railway variables set SMTP_SERVER_ALT=smtp.gmail.com
railway variables set SMTP_PORT_ALT=465

# ---------- Resend (optional – set if you have a key) ----------
# Uncomment and fill in if you sign up at https://resend.com
# railway variables set RESEND_API_KEY=re_YOUR_KEY_HERE
# railway variables set RESEND_FROM_EMAIL=info@yourbudgetpulse.online
# railway variables set RESEND_FROM_NAME="Budget Pulse"

echo ""
echo "Done! Verify at: https://railway.app/project/94744993-bec7-4bd4-8f02-ca0758880a09"
echo ""
echo "Then test from the admin panel:"
echo "  POST /admin/test-email    – sends a test email to your admin account"
echo "  GET  /admin/email-config  – shows current configuration status"
