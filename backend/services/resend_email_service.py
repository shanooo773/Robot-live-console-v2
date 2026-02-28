"""
Resend Email Service - Handles transactional email delivery via Resend API.
Uses RESEND_API_KEY and MAIL_FROM environment variables.
"""

import os
import logging

logger = logging.getLogger(__name__)


class ResendEmailService:
    """Email service backed by the Resend API (https://resend.com)."""

    def __init__(self):
        api_key = os.getenv('RESEND_API_KEY')
        if not api_key:
            logger.warning(
                "⚠️ RESEND_API_KEY not configured. Email sending will be disabled."
            )
            self.enabled = False
            self._resend = None
            return

        try:
            import resend as resend_module  # type: ignore
            resend_module.api_key = api_key
            self._resend = resend_module
            self.enabled = True
        except ImportError:
            logger.error(
                "❌ 'resend' package not installed. Run: pip install resend"
            )
            self.enabled = False
            self._resend = None
            return

        self.mail_from = os.getenv(
            'MAIL_FROM',
            'no-reply@contact.anybot.brainswarmrobotics.com'
        )
        logger.info(f"✅ Resend email service initialised (from: {self.mail_from})")

    async def send_confirmation_email(
        self, email: str, confirmation_url: str, name: str = "User"
    ):
        """Send an email-confirmation message to a newly registered user."""
        if not self.enabled:
            logger.warning(
                f"⚠️ Email sending disabled. Confirmation URL for {email}: {confirmation_url}"
            )
            return

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
                        This link will expire in 1 hour. If you did not create an account,
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

        try:
            self._resend.Emails.send({
                "from": self.mail_from,
                "to": [email],
                "subject": "Confirm Your Email - Robot Live Console",
                "html": html,
            })
            logger.info(f"✅ Confirmation email sent to: {email}")
        except Exception as e:
            logger.error(f"❌ Failed to send confirmation email to {email}: {e}")

    async def send_password_reset_email(
        self, email: str, reset_url: str, name: str = "User"
    ):
        """Send a password-reset link to the user."""
        if not self.enabled:
            logger.warning(
                f"⚠️ Email sending disabled. Password reset URL for {email}: {reset_url}"
            )
            return

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Password Reset Request</h2>
                    <p>Hi {name},</p>
                    <p>We received a request to reset your password for Robot Live Console.
                       Click the button below to reset your password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}"
                           style="background-color: #2563eb; color: white; padding: 12px 30px;
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666;">{reset_url}</p>
                    <p style="margin-top: 30px; font-size: 0.9em; color: #666;">
                        This link will expire in 1 hour. If you did not request a password reset,
                        you can safely ignore this email. Your password will not be changed.
                    </p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="font-size: 0.8em; color: #999;">
                        Robot Live Console - Your Remote Robot Programming Platform
                    </p>
                </div>
            </body>
        </html>
        """

        try:
            self._resend.Emails.send({
                "from": self.mail_from,
                "to": [email],
                "subject": "Password Reset - Robot Live Console",
                "html": html,
            })
            logger.info(f"✅ Password reset email sent to: {email}")
        except Exception as e:
            logger.error(f"❌ Failed to send password reset email to {email}: {e}")
