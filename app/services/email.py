import smtplib
import secrets
import asyncio
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

    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send email using SMTP"""
        try:
            print(f"📧 Attempting to send email to {to_email}")
            print(f"📧 SMTP Server: {self.smtp_server}:{self.smtp_port}")
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
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    print(f"🔐 Starting TLS...")
                    server.starttls()
                    print(f"🔑 Logging in with {self.username}...")
                    server.login(self.username, self.password)
                    print(f"📤 Sending message...")
                    server.send_message(msg)
                    print(f"✅ Message sent successfully!")
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, send_smtp)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Email sending failed to {to_email}: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
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