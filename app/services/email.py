import smtplib
import secrets
import asyncio
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict
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
        # Skip email sending in development mode
        self.is_development = settings.ENV == "development" or "localhost" in settings.DATABASE_URL
        
        # Alternative SMTP settings
        self.smtp_server_alt = getattr(settings, 'SMTP_SERVER_ALT', 'smtp.talivio.com')
        self.smtp_port_alt = getattr(settings, 'SMTP_PORT_ALT', 465)
        
        # Resend settings for production
        self.resend_api_key = getattr(settings, 'RESEND_API_KEY', None)
        self.resend_from_email = getattr(settings, 'RESEND_FROM_EMAIL', None) or self.from_email
        self.resend_from_name = getattr(settings, 'RESEND_FROM_NAME', None) or self.from_name

    async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send email using Resend API in production, SMTP in development"""
        
        # Skip email sending in development mode
        if self.is_development:
            print(f"Development mode: Skipping email to {to_email}")
            print(f"Subject: {subject}")
            print(f"Content preview: {html_content[:100]}...")
            return True
        
        # Use Resend API if available (preferred method)
        if self.resend_api_key:
            print(f"Using Resend API for email...")
            return await self._send_email_resend(to_email, subject, html_content, text_content)
        
        # Fallback to SMTP if Resend is not configured
        print(f"Using SMTP for email...")
        
        # Try primary SMTP server first (Google SMTP with TLS)
        result = await self._try_send_email(to_email, subject, html_content, text_content, 
                                          self.smtp_server, self.smtp_port, use_ssl=False)
        if result:
            return True
            
        # Try alternative SMTP server (Google SMTP with SSL)
        print(f"Trying alternative SMTP server (SSL)...")
        result = await self._try_send_email(to_email, subject, html_content, text_content, 
                                          self.smtp_server_alt, self.smtp_port_alt, use_ssl=True)
        return result

    async def _send_email_resend(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send email using Resend API"""
        try:
            print(f"Sending email via Resend to {to_email}")
            print(f"From: {self.resend_from_name} <{self.resend_from_email}>")
            print(f"Subject: {subject}")
            
            # Prepare email data for Resend API
            email_data = {
                "from": f"{self.resend_from_name} <{self.resend_from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            
            # Add text content if provided
            if text_content:
                email_data["text"] = text_content
            
            # Send via Resend API
            headers = {
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers=headers,
                    json=email_data
                )
                
                if response.status_code == 200:
                    print(f"Email sent successfully via Resend to {to_email}")
                    return True
                else:
                    print(f"Resend API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Resend email sending failed to {to_email}: {e}")
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
    
    async def send_weekly_report_email(self, user_email: str, user_name: str, report: Dict):
        """Send weekly financial report email"""
        period = report['period']
        summary = report['summary']
        insights = report['insights']
        achievements = report['achievements']
        recommendations = report['recommendations']
        currency_code = report.get('currency', 'USD')

        # Get currency symbol from the CURRENCIES dictionary
        from app.core.currency import CURRENCIES
        currency_info = CURRENCIES.get(currency_code, CURRENCIES['USD'])
        currency_symbol = currency_info['symbol']
        currency_position = currency_info.get('position', 'before')

        # Helper function to format amounts with correct currency
        def format_currency(amount):
            if currency_position == 'before':
                return f"{currency_symbol}{amount:.2f}"
            else:
                return f"{amount:.2f}{currency_symbol}"

        subject = f"Your Weekly Financial Report - Week of {period['start']}"
        
        # Build insights HTML
        insights_html = ""
        for insight in insights:
            # Remove emoji for cleaner HTML, then add back with styling
            insight_text = insight
            insights_html += f"<li style='margin-bottom: 10px;'>{insight_text}</li>"
        
        # Build achievements HTML
        achievements_html = ""
        if achievements:
            for achievement in achievements:
                achievements_html += f"""
                <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 15px; margin-bottom: 10px; border-radius: 5px;">
                    <strong style="color: #10b981;">{achievement['title']}</strong>
                    <p style="margin: 5px 0 0 0; color: #374151;">{achievement['description']}</p>
                </div>
                """
        
        # Build recommendations HTML
        recommendations_html = ""
        if recommendations:
            for rec in recommendations[:3]:  # Top 3 recommendations
                priority_color = {'high': '#ef4444', 'medium': '#f59e0b', 'low': '#10b981'}.get(rec.get('priority', 'low'), '#10b981')
                recommendations_html += f"""
                <div style="background: #f9fafb; border-left: 4px solid {priority_color}; padding: 15px; margin-bottom: 10px; border-radius: 5px;">
                    <strong style="color: {priority_color};">{rec['title']}</strong>
                    <p style="margin: 5px 0 0 0; color: #374151;">{rec['description']}</p>
                </div>
                """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #1f2937; background: #f3f4f6; }}
                .container {{ max-width: 650px; margin: 20px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 700; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }}
                .content {{ padding: 30px; }}
                .summary-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .summary-card {{ background: #f9fafb; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #e5e7eb; }}
                .summary-card .label {{ font-size: 14px; color: #6b7280; margin-bottom: 8px; }}
                .summary-card .value {{ font-size: 24px; font-weight: 700; color: #1f2937; }}
                .summary-card.positive .value {{ color: #10b981; }}
                .summary-card.negative .value {{ color: #ef4444; }}
                .section {{ margin: 30px 0; }}
                .section-title {{ font-size: 20px; font-weight: 600; color: #1f2937; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #e5e7eb; }}
                .insight-list {{ list-style: none; padding: 0; }}
                .insight-list li {{ background: #f9fafb; padding: 12px 15px; margin-bottom: 8px; border-radius: 6px; border-left: 3px solid #667eea; }}
                .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
                .cta-button {{ display: inline-block; padding: 14px 28px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
                .cta-button:hover {{ background: #5568d3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Weekly Financial Report</h1>
                    <p>Week of {period['start']} to {period['end']}</p>
                </div>
                
                <div class="content">
                    <!-- Summary Section -->
                    <div class="section">
                        <div class="summary-grid">
                            <div class="summary-card negative">
                                <div class="label">Total Expenses</div>
                                <div class="value">{format_currency(summary['total_expenses'])}</div>
                            </div>
                            <div class="summary-card positive">
                                <div class="label">Total Income</div>
                                <div class="value">{format_currency(summary['total_income'])}</div>
                            </div>
                            <div class="summary-card {'positive' if summary['net_savings'] > 0 else 'negative'}">
                                <div class="label">Net Savings</div>
                                <div class="value">{format_currency(summary['net_savings'])}</div>
                            </div>
                            <div class="summary-card">
                                <div class="label">Transactions</div>
                                <div class="value">{summary['transaction_count']}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Key Insights -->
                    <div class="section">
                        <h2 class="section-title">Key Insights</h2>
                        <ul class="insight-list">
                            {insights_html}
                        </ul>
                    </div>
                    
                    <!-- Achievements -->
                    {"<div class='section'><h2 class='section-title'>Achievements</h2>" + achievements_html + "</div>" if achievements else ""}
                    
                    <!-- Recommendations -->
                    {"<div class='section'><h2 class='section-title'>Recommendations</h2>" + recommendations_html + "</div>" if recommendations else ""}
                    
                    <!-- CTA -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.BASE_URL}/" class="cta-button">View Full Dashboard</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Keep tracking your finances and stay on top of your goals!</p>
                    <p style="margin-top: 15px;">
                        <a href="{settings.BASE_URL}/ai/settings" style="color: #667eea; text-decoration: none;">Manage Report Settings</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text fallback
        from app.services.weekly_report_service import WeeklyReportService
        text_content = WeeklyReportService(self.db).format_report_text(report) if hasattr(self, 'db') else "View your weekly report online."
        
        return await self.send_email(user_email, subject, html_content, text_content)
    
    async def send_monthly_report_email(self, user_email: str, user_name: str, report: Dict):
        """Send monthly financial report email"""
        period = report['period']
        summary = report['summary']
        insights = report['insights']
        achievements = report['achievements']
        recommendations = report['recommendations']
        currency_code = report.get('currency', 'USD')

        # Get currency symbol from the CURRENCIES dictionary
        from app.core.currency import CURRENCIES
        currency_info = CURRENCIES.get(currency_code, CURRENCIES['USD'])
        currency_symbol = currency_info['symbol']
        currency_position = currency_info.get('position', 'before')

        # Helper function to format amounts with correct currency
        def format_currency(amount):
            if currency_position == 'before':
                return f"{currency_symbol}{amount:.2f}"
            else:
                return f"{amount:.2f}{currency_symbol}"

        subject = f"Your Monthly Financial Report - {period['month_name']} {period['year']}"
        
        # Build insights HTML
        insights_html = ""
        for insight in insights:
            insight_text = insight
            insights_html += f"<li style='margin-bottom: 10px;'>{insight_text}</li>"
        
        # Build achievements HTML
        achievements_html = ""
        if achievements:
            for achievement in achievements:
                achievements_html += f"""
                <div style='background: #d4edda; padding: 15px; margin-bottom: 10px; border-radius: 6px; border-left: 4px solid #28a745;'>
                    <strong style='color: #155724;'>{achievement['title']}</strong><br>
                    <span style='color: #155724;'>{achievement['description']}</span>
                </div>
                """
        
        # Build recommendations HTML
        recommendations_html = ""
        if recommendations:
            for rec in recommendations:
                priority_color = "#dc3545" if rec.get('priority') == 'high' else "#ffc107"
                recommendations_html += f"""
                <div style='background: #fff3cd; padding: 15px; margin-bottom: 10px; border-radius: 6px; border-left: 4px solid {priority_color};'>
                    <strong style='color: #856404;'>{rec['title']}</strong><br>
                    <span style='color: #856404;'>{rec['description']}</span>
                </div>
                """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Monthly Financial Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 30px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 30px; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin: 20px 0; }}
                .summary-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .summary-card .label {{ font-size: 14px; color: #6b7280; margin-bottom: 8px; }}
                .summary-card .value {{ font-size: 24px; font-weight: 700; color: #1f2937; }}
                .summary-card.positive .value {{ color: #10b981; }}
                .summary-card.negative .value {{ color: #ef4444; }}
                .section {{ margin: 30px 0; }}
                .section-title {{ font-size: 20px; font-weight: 600; color: #1f2937; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #e5e7eb; }}
                .insight-list {{ list-style: none; padding: 0; }}
                .insight-list li {{ background: #f9fafb; padding: 12px 15px; margin-bottom: 8px; border-radius: 6px; border-left: 3px solid #667eea; }}
                .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
                .cta-button {{ display: inline-block; padding: 14px 28px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
                .cta-button:hover {{ background: #5568d3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Monthly Financial Report</h1>
                    <p>{period['month_name']} {period['year']}</p>
                </div>
                
                <div class="content">
                    <!-- Summary Section -->
                    <div class="section">
                        <div class="summary-grid">
                            <div class="summary-card positive">
                                <div class="label">Total Income</div>
                                <div class="value">{format_currency(summary['total_income'])}</div>
                            </div>
                            <div class="summary-card negative">
                                <div class="label">Total Expenses</div>
                                <div class="value">{format_currency(summary['total_expenses'])}</div>
                            </div>
                            <div class="summary-card {'positive' if summary['net_savings'] > 0 else 'negative'}">
                                <div class="label">Net Savings</div>
                                <div class="value">{format_currency(summary['net_savings'])}</div>
                            </div>
                            <div class="summary-card">
                                <div class="label">Savings Rate</div>
                                <div class="value">{summary['savings_rate']:.1f}%</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Key Insights -->
                    <div class="section">
                        <h2 class="section-title">Key Insights</h2>
                        <ul class="insight-list">
                            {insights_html}
                        </ul>
                    </div>
                    
                    {f'<!-- Achievements --><div class="section"><h2 class="section-title">Achievements</h2>{achievements_html}</div>' if achievements_html else ''}
                    
                    {f'<!-- Recommendations --><div class="section"><h2 class="section-title">Recommendations</h2>{recommendations_html}</div>' if recommendations_html else ''}
                    
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="https://yourbudgetpulse.online/reports/monthly" class="cta-button">View Full Report</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This report was generated automatically by your Expense Manager.</p>
                    <p>For support, contact us at support@yourbudgetpulse.online</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text fallback
        text_content = f"""
        Your Monthly Financial Report - {period['month_name']} {period['year']}

        Income: {format_currency(summary['total_income'])}
        Expenses: {format_currency(summary['total_expenses'])}
        Net Savings: {format_currency(summary['net_savings'])}
        Savings Rate: {summary['savings_rate']:.1f}%

        Key Insights:
        {chr(10).join(insights)}

        View your full report at: https://yourbudgetpulse.online/reports/monthly
        """
        
        return await self.send_email(user_email, subject, html_content, text_content)
    
    async def send_annual_report_email(self, user_email: str, user_name: str, report: Dict):
        """Send annual financial report email"""
        period = report['period']
        summary = report['summary']
        currency_code = report.get('currency', 'USD')

        # Get currency symbol from the CURRENCIES dictionary
        from app.core.currency import CURRENCIES
        currency_info = CURRENCIES.get(currency_code, CURRENCIES['USD'])
        currency_symbol = currency_info['symbol']
        currency_position = currency_info.get('position', 'before')

        # Helper function to format amounts with correct currency
        def format_currency(amount):
            if currency_position == 'before':
                return f"{currency_symbol}{amount:.2f}"
            else:
                return f"{amount:.2f}{currency_symbol}"

        subject = f"Your Annual Financial Report - {period['year']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Annual Financial Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 30px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 30px; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin: 20px 0; }}
                .summary-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .summary-card .label {{ font-size: 14px; color: #6b7280; margin-bottom: 8px; }}
                .summary-card .value {{ font-size: 24px; font-weight: 700; color: #1f2937; }}
                .summary-card.positive .value {{ color: #10b981; }}
                .summary-card.negative .value {{ color: #ef4444; }}
                .section {{ margin: 30px 0; }}
                .section-title {{ font-size: 20px; font-weight: 600; color: #1f2937; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #e5e7eb; }}
                .footer {{ background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
                .cta-button {{ display: inline-block; padding: 14px 28px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
                .cta-button:hover {{ background: #5568d3; }}
                .coming-soon {{ background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Annual Financial Report</h1>
                    <p>{period['year']}</p>
                </div>
                
                <div class="content">
                    <!-- Summary Section -->
                    <div class="section">
                        <div class="summary-grid">
                            <div class="summary-card positive">
                                <div class="label">Total Income</div>
                                <div class="value">{format_currency(summary['income'])}</div>
                            </div>
                            <div class="summary-card negative">
                                <div class="label">Total Expenses</div>
                                <div class="value">{format_currency(summary['expense'])}</div>
                            </div>
                            <div class="summary-card {'positive' if summary['balance'] > 0 else 'negative'}">
                                <div class="label">Net Balance</div>
                                <div class="value">{format_currency(summary['balance'])}</div>
                            </div>
                            <div class="summary-card">
                                <div class="label">Year</div>
                                <div class="value">{period['year']}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="coming-soon">
                        <h3 style="color: #856404; margin-top: 0;">Advanced Annual Reports Coming Soon!</h3>
                        <p style="color: #856404; margin-bottom: 0;">
                            We're working on comprehensive annual reports with year-over-year comparisons, 
                            seasonal analysis, and detailed insights. Stay tuned for more features!
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="https://yourbudgetpulse.online/reports/annual" class="cta-button">View Full Report</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This report was generated automatically by your Expense Manager.</p>
                    <p>For support, contact us at support@yourbudgetpulse.online</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text fallback
        text_content = f"""
        Your Annual Financial Report - {period['year']}

        Income: {format_currency(summary['income'])}
        Expenses: {format_currency(summary['expense'])}
        Net Balance: {format_currency(summary['balance'])}

        Advanced annual reports with year-over-year comparisons and seasonal analysis are coming soon!

        View your full report at: https://yourbudgetpulse.online/reports/annual
        """
        
        return await self.send_email(user_email, subject, html_content, text_content)

# Global service instance
email_service = EmailService()