"""
Mail Service - Handles email sending for confirmation emails
Uses fastapi-mail for SMTP email delivery
"""

import os
import logging
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MailService:
    """Service for sending emails"""
    
    def __init__(self):
        """Initialize MailService with SMTP configuration from environment"""
        
        # Get SMTP configuration from environment
        mail_username = os.getenv('MAIL_USERNAME', '')
        mail_password = os.getenv('MAIL_PASSWORD', '')
        mail_from = os.getenv('MAIL_FROM', mail_username if mail_username else 'noreply@example.com')
        mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.getenv('MAIL_PORT', '587'))
        mail_starttls = os.getenv('MAIL_STARTTLS', 'true').lower() == 'true'
        mail_ssl_tls = os.getenv('MAIL_SSL_TLS', 'false').lower() == 'true'
        
        # Validate required configuration
        if not mail_username or not mail_password:
            logger.warning("⚠️ MAIL_USERNAME or MAIL_PASSWORD not configured. Email sending will be disabled.")
            self.enabled = False
            self.fastmail = None
            return
        else:
            self.enabled = True
        
        # Configure FastMail only if credentials are available
        self.conf = ConnectionConfig(
            MAIL_USERNAME=mail_username,
            MAIL_PASSWORD=mail_password,
            MAIL_FROM=mail_from,
            MAIL_PORT=mail_port,
            MAIL_SERVER=mail_server,
            MAIL_STARTTLS=mail_starttls,
            MAIL_SSL_TLS=mail_ssl_tls,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        
        self.fastmail = FastMail(self.conf)
        
        logger.info(f"✅ Mail service initialized with server: {mail_server}:{mail_port}")
    
    async def send_confirmation_email(self, email: str, confirmation_url: str, name: str = "User"):
        """
        Send email confirmation to a user
        
        Args:
            email: Recipient email address
            confirmation_url: Full URL for email confirmation
            name: User's name for personalization
        """
        if not self.enabled:
            logger.warning(f"⚠️ Email sending disabled. Would send confirmation to: {email}")
            logger.info(f"📧 Confirmation URL: {confirmation_url}")
            return
        
        try:
            # Create HTML email body
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2563eb;">Welcome to Robot Live Console!</h2>
                        <p>Hi {name},</p>
                        <p>Thank you for registering! Please confirm your email address by clicking the button below:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{confirmation_url}" 
                               style="background-color: #2563eb; color: white; padding: 12px 30px; 
                                      text-decoration: none; border-radius: 5px; display: inline-block;">
                                Confirm Email Address
                            </a>
                        </div>
                        <p>Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #666;">{confirmation_url}</p>
                        <p style="margin-top: 30px; font-size: 0.9em; color: #666;">
                            This link will expire in 1 hour. If you didn't create an account, 
                            you can safely ignore this email.
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        <p style="font-size: 0.8em; color: #999;">
                            Robot Live Console - Your Remote Robot Programming Platform
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Create plain text version as fallback
            text = f"""
            Welcome to Robot Live Console!
            
            Hi {name},
            
            Thank you for registering! Please confirm your email address by visiting this link:
            
            {confirmation_url}
            
            This link will expire in 1 hour. If you didn't create an account, you can safely ignore this email.
            
            ---
            Robot Live Console - Your Remote Robot Programming Platform
            """
            
            message = MessageSchema(
                subject="Confirm Your Email - Robot Live Console",
                recipients=[email],
                body=html,
                subtype=MessageType.html
            )
            
            await self.fastmail.send_message(message)
            logger.info(f"✅ Confirmation email sent to: {email}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send confirmation email to {email}: {e}")
            # Don't raise exception - we want registration to continue even if email fails
            # The confirmation URL is also returned in the response for development/testing
