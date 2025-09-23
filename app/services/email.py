import smtplib
import secrets
import asyncio
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME
        
        # Alternative SMTP settings
        self.smtp_server_alt = getattr(settings, 'SMTP_SERVER_ALT', 'smtp.talivio.com')
        self.smtp_port_alt = getattr(settings, 'SMTP_PORT_ALT', 465)
        
        # SendGrid settings for production
        self.sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.sendgrid_from_email = getattr(settings, 'SENDGRID_FROM_EMAIL', self.from_email)
        self.sendgrid_from_name = getattr(settings, 'SENDGRID_FROM_NAME', self.from_name)

    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send email using SendGrid API in production, SMTP in development"""
        
        # Use SendGrid for production environments
        if settings.ENV == "production" and self.sendgrid_api_key:
            print(f"📧 Using SendGrid API for production email...")
            return await self._send_email_sendgrid(to_email, subject, html_content, text_content)
        
        # Fallback to SMTP for development
        print(f"📧 Using SMTP for development email...")
        
        # Try primary SMTP server first (Google SMTP with TLS)
        result = await self._try_send_email(to_email, subject, html_content, text_content, 
                                          self.smtp_server, self.smtp_port, use_ssl=False)
        if result:
            return True
            
        # Try alternative SMTP server (Google SMTP with SSL)
        print(f"🔄 Trying alternative SMTP server (SSL)...")
        result = await self._try_send_email(to_email, subject, html_content, text_content, 
                                          self.smtp_server_alt, self.smtp_port_alt, use_ssl=True)
        return result

    async def _send_email_sendgrid(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send email using SendGrid API"""
        try:
            print(f"📧 Sending email via SendGrid to {to_email}")
            print(f"📧 From: {self.sendgrid_from_name} <{self.sendgrid_from_email}>")
            print(f"📧 Subject: {subject}")
            
            # Prepare email data for SendGrid API
            email_data = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}]
                    }
                ],
                "from": {
                    "email": self.sendgrid_from_email,
                    "name": self.sendgrid_from_name
                },
                "subject": subject,
                "content": [
                    {
                        "type": "text/html",
                        "value": html_content
                    }
                ]
            }
            
            # Add text content if provided
            if text_content:
                email_data["content"].insert(0, {
                    "type": "text/plain",
                    "value": text_content
                })
            
            # Send via SendGrid API
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers=headers,
                    json=email_data
                )
                
                if response.status_code == 202:
                    print(f"✅ Email sent successfully via SendGrid to {to_email}")
                    return True
                else:
                    print(f"❌ SendGrid API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ SendGrid email sending failed to {to_email}: {e}")
            return False

    async def _try_send_email(self, to_email: str, subject: str, html_content: str, text_content: str, 
                            smtp_server: str, smtp_port: int, use_ssl: bool = False):
        """Try sending email with specific SMTP settings"""
        max_retries = 2
        retry_delay = 3  # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"📧 Attempting to send email to {to_email} (attempt {attempt + 1}/{max_retries})")
                print(f"📧 SMTP Server: {smtp_server}:{smtp_port} (SSL: {use_ssl})")
                print(f"📧 From: {self.from_name} <{self.from_email}>")
                print(f"📧 Subject: {subject}")
                
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = f"{self.from_name} <{self.from_email}>"
                msg['To'] = to_email

                # Add text and HTML parts
                if text_content:
                    text_part = MIMEText(text_content, 'plain')
                    msg.attach(text_part)
                
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)

                # Send email in thread to avoid blocking
                def send_smtp():
                    print(f"🔌 Connecting to SMTP server...")
                    try:
                        if use_ssl:
                            # Use SSL connection
                            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
                            print(f"🔌 Connected via SSL to {smtp_server}:{smtp_port}")
                        else:
                            # Use TLS connection
                            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                            print(f"🔌 Connected to {smtp_server}:{smtp_port}")
                            print(f"🔐 Starting TLS...")
                            server.starttls()
                        
                        print(f"🔑 Logging in with {self.username}...")
                        server.login(self.username, self.password)
                        print(f"📤 Sending message...")
                        print(f"📧 Message details:")
                        print(f"   From: {msg['From']}")
                        print(f"   To: {msg['To']}")
                        print(f"   Subject: {msg['Subject']}")
                        server.send_message(msg)
                        print(f"✅ Message sent successfully!")
                        server.quit()
                    except Exception as e:
                        print(f"❌ SMTP error: {e}")
                        raise
                
                # Run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, send_smtp)
                
                print(f"✅ Email sent successfully to {to_email}")
                return True
                
            except Exception as e:
                print(f"❌ Email sending failed to {to_email} (attempt {attempt + 1}): {e}")
                print(f"❌ Error type: {type(e).__name__}")
                
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"❌ All {max_retries} attempts failed for {smtp_server}")
                    import traceback
                    print(f"❌ Final traceback: {traceback.format_exc()}")
                    return False

    async def send_confirmation_email(self, user_email: str, confirmation_token: str):
        """Send email confirmation"""
        confirmation_url = f"{settings.BASE_URL}/confirm-email/{confirmation_token}"
        
        subject = "Confirm Your Email - Budget Pulse"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Budget Pulse!</h1>
                </div>
                <div class="content">
                    <h2>Please confirm your email address</h2>
                    <p>Thank you for signing up for Budget Pulse. To complete your registration and start managing your finances, please click the button below to confirm your email address:</p>
                    
                    <a href="{confirmation_url}" class="button">Confirm Email Address</a>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{confirmation_url}</p>
                    
                    <p>This link will expire in 24 hours for security reasons.</p>
                    
                    <p>If you didn't create an account with Budget Pulse, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2024 Budget Pulse. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Budget Pulse!
        
        Please confirm your email address by visiting: {confirmation_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        """
        
        return await self.send_email(user_email, subject, html_content, text_content)

    async def send_password_reset_email(self, user_email: str, reset_token: str):
        """Send password reset email"""
        reset_url = f"{settings.BASE_URL}/reset-password/{reset_token}"
        
        subject = "Reset Your Password - Budget Pulse"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #ef4444; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; text-align: center; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Reset your password</h2>
                    <p>You requested to reset your password for your Budget Pulse account. Click the button below to set a new password:</p>
                    
                    <a href="{reset_url}" class="button">Reset Password</a>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #ef4444;">{reset_url}</p>
                    
                    <p><strong>This link will expire in 1 hour for security reasons.</strong></p>
                    
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>© 2024 Budget Pulse. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Reset your password by visiting: {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        """
        
        return await self.send_email(user_email, subject, html_content, text_content)

# Global service instance
email_service = EmailService()