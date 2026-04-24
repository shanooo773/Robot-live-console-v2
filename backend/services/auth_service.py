"""
Authentication Service - Handles user authentication and authorization
This service is completely independent of Docker and should always be available.
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException
from auth import auth_manager
from database import DatabaseManager
from services.token_service import TokenService
from services.resend_email_service import ResendEmailService

logger = logging.getLogger(__name__)

class AuthServiceException(Exception):
    """Exception raised when authentication service encounters an error"""
    pass

class AuthService:
    """
    Service for handling user authentication and authorization.
    This service operates independently of Docker and other services.
    """
    
    def __init__(self, db: DatabaseManager, theia_manager=None):
        self.db = db
        self.auth_manager = auth_manager
        self.available = True
        self.status = "available"
        self.theia_manager = theia_manager
        
        # Initialize token and mail services
        self.token_service = TokenService()
        self.mail_service = ResendEmailService()
        
        # Public base URL of the frontend application (used to build verification/reset links)
        self.app_public_base_url = os.getenv(
            "APP_PUBLIC_BASE_URL",
            os.getenv("SERVER_HOST", "http://localhost:3000")
        )
        
        logger.info("✅ Auth service initialized successfully")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": "auth",
            "available": self.available,
            "status": self.status,
            "features": ["registration", "login", "jwt_tokens", "role_management", "email_confirmation", "google_oauth"]
        }
    
    async def send_confirmation_email(self, email: str, name: str) -> str:
        """
        Send confirmation email to user
        
        Args:
            email: User's email address
            name: User's name
            
        Returns:
            Confirmation URL (for development/testing)
        """
        try:
            # Generate confirmation token
            token = self.token_service.generate_confirmation_token(email)
            
            # Build frontend verification URL (frontend handles the redirect)
            confirmation_url = f"{self.app_public_base_url}/verify-email?token={token}"
            
            # Send email asynchronously
            await self.mail_service.send_confirmation_email(email, confirmation_url, name)
            
            return confirmation_url
        except Exception as e:
            logger.error(f"❌ Failed to send confirmation email for {email}: {e}")
            raise
    
    async def register_user(self, name: str, email: str, password: str, background_tasks=None) -> Dict[str, Any]:
        """Register a new user and send confirmation email (no immediate JWT)"""
        try:
            logger.info(f"📝 Registration attempt for email: {email}")
            user = self.db.create_user(name, email, password)
            logger.info(f"✅ User registered successfully: {email} (ID: {user['id']})")
            
            # Generate confirmation token
            token = self.token_service.generate_confirmation_token(user['email'])
            confirmation_url = f"{self.app_public_base_url}/verify-email?token={token}"
            
            # Send confirmation email in background if BackgroundTasks provided
            if background_tasks:
                background_tasks.add_task(
                    self.mail_service.send_confirmation_email,
                    user['email'], 
                    confirmation_url, 
                    user['name']
                )
            else:
                # Fallback to synchronous email sending
                await self.send_confirmation_email(user['email'], user['name'])
            
            # Return success message without JWT
            return {
                "message": "Registration successful! Please check your email to confirm your account.",
                "email": user['email'],
                "confirm_url": confirmation_url,  # Include for dev/testing
                "user": {
                    "id": user['id'],
                    "name": user['name'],
                    "email": user['email'],
                    "role": user['role'],
                    "is_active": False
                }
            }
        except ValueError as e:
            logger.warning(f"⚠️ Registration failed for {email}: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"❌ Registration failed with exception for {email}: {e}")
            raise AuthServiceException(f"Registration failed: {str(e)}")
    
    def confirm_email(self, token: str) -> Dict[str, Any]:
        """
        Confirm user email with token
        
        Args:
            token: Email confirmation token
            
        Returns:
            Success message and user info
        """
        try:
            # Validate token and get email
            email = self.token_service.validate_confirmation_token(token)
            
            # Activate user
            success = self.db.activate_user_by_email(email)
            
            if not success:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get updated user info
            user = self.db.get_user_by_email(email)
            
            logger.info(f"✅ Email confirmed for: {email}")
            
            return {
                "message": "Email confirmed successfully! You can now log in.",
                "user": {
                    "id": user['id'],
                    "name": user['name'],
                    "email": user['email'],
                    "role": user['role'],
                    "is_active": True
                }
            }
        except ValueError as e:
            # Token validation errors (expired, invalid)
            logger.warning(f"⚠️ Email confirmation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Email confirmation failed with exception: {e}")
            raise AuthServiceException(f"Email confirmation failed: {str(e)}")
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and return token (requires email confirmation)"""
        try:
            logger.info(f"🔐 Login attempt for email: {email}")
            
            # Authenticate against database
            logger.info(f"📊 Checking database authentication for: {email}")
            user = self.db.authenticate_user(email, password)
            if not user:
                logger.warning(f"❌ Database authentication failed for: {email}")
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            # Check if user's email is confirmed
            if not user.get('is_active', False):
                logger.warning(f"⚠️ Login attempt for unconfirmed email: {email}")
                raise HTTPException(
                    status_code=403, 
                    detail="Email not confirmed. Please check your inbox for a confirmation link."
                )
            
            logger.info(f"✅ Database authentication successful for: {email} (ID: {user['id']}, Role: {user['role']})")
            
            # Update user activity tracking
            self.db.update_user_activity(user['id'], 'login')
            
            # Ensure user onboarding setup (theia port assignment and directory creation)
            self._ensure_user_onboarding(user['id'], user['email'])
            
            token = self.auth_manager.create_access_token(
                data={"sub": str(user["id"]), "email": user["email"], "role": user["role"]}
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": user
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Login failed with exception for {email}: {e}")
            raise AuthServiceException(f"Login failed: {str(e)}")
    
    def get_user_by_token(self, token_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get user information from token data"""
        try:
            user_id = int(token_data["sub"])
            user = self.db.get_user_by_id(user_id)
            if not user:
                return None
            return user
        except Exception as e:
            logger.error(f"Failed to get user by token: {e}")
            return None
    
    def verify_admin_role(self, user: Dict[str, Any]) -> bool:
        """Verify if user has admin role"""
        return user.get("role") == "admin"
    
    def login_with_google(self, id_token: str) -> Dict[str, Any]:
        """
        Login or register user with Google OAuth
        
        Args:
            id_token: Google ID token from client
            
        Returns:
            JWT token and user info
        """
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests
            
            # Get Google Client ID from environment
            google_client_id = os.getenv('GOOGLE_CLIENT_ID')
            if not google_client_id:
                logger.error("❌ GOOGLE_CLIENT_ID not configured")
                raise HTTPException(
                    status_code=500, 
                    detail="Google OAuth not configured. Please contact administrator."
                )
            
            logger.info("🔐 Google OAuth login attempt")

            # Verify the Google ID token
            try:
                import requests as http_requests
                from google.auth import exceptions as google_exceptions

                # Short-timeout transport — default is 120s which hangs the event loop
                class _ShortTimeoutRequest(requests.Request):
                    def __call__(self, url, method="GET", body=None, headers=None, timeout=10, **kwargs):
                        return super().__call__(url, method=method, body=body, headers=headers, timeout=timeout, **kwargs)

                idinfo = google_id_token.verify_oauth2_token(
                    id_token,
                    _ShortTimeoutRequest(),
                    google_client_id
                )

                # Check if Google email is verified
                if idinfo.get("email_verified") is not True:
                    logger.warning("⚠️ Unverified Google email attempted login")
                    raise HTTPException(
                        status_code=401,
                        detail="Google email not verified. Please verify your email with Google first."
                    )

                # Extract user information from Google token
                google_user_id = idinfo['sub']
                email = idinfo.get('email')

                if not email:
                    raise HTTPException(status_code=400, detail="Email not provided by Google")

                name = idinfo.get('name', email.split('@')[0])

                logger.info(f"✅ Google token verified for: {email}")

            except HTTPException:
                raise
            except ValueError as e:
                logger.warning(f"⚠️ Invalid Google token: {e}")
                raise HTTPException(status_code=401, detail="Invalid Google token")
            except (http_requests.exceptions.Timeout, http_requests.exceptions.ConnectionError) as e:
                logger.error(f"❌ Could not reach Google cert endpoint: {e}")
                raise HTTPException(status_code=503, detail="Google verification service unreachable. Please try again.")
            except google_exceptions.TransportError as e:
                logger.error(f"❌ Google transport error: {e}")
                raise HTTPException(status_code=503, detail="Google verification service unreachable. Please try again.")
            
            # Upsert user in database (create or update)
            user = self.db.upsert_google_user(email, name, google_user_id)
            logger.info(f"✅ Google user upserted: {email} (ID: {user['id']})")
            
            # Ensure user onboarding setup
            self._ensure_user_onboarding(user['id'], user['email'])
            
            # Create JWT token
            token = self.auth_manager.create_access_token(
                data={"sub": str(user["id"]), "email": user["email"], "role": user["role"]}
            )
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": user
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Google OAuth login failed: {e}")
            raise AuthServiceException(f"Google OAuth login failed: {str(e)}")
    
    def login_with_github(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Login or register user with GitHub OAuth code"""
        import httpx

        github_client_id = os.getenv('GITHUB_CLIENT_ID')
        github_client_secret = os.getenv('GITHUB_CLIENT_SECRET')

        if not github_client_id or not github_client_secret:
            logger.error("❌ GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET not configured")
            raise HTTPException(status_code=500, detail="GitHub OAuth not configured.")

        logger.info("🔐 GitHub OAuth login attempt")

        try:
            token_request_data = {
                "client_id": github_client_id,
                "client_secret": github_client_secret,
                "code": code,
            }
            if redirect_uri:
                token_request_data["redirect_uri"] = redirect_uri

            # Exchange code for access token
            token_response = httpx.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data=token_request_data,
                timeout=10,
            )
            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                logger.warning(f"⚠️ GitHub token exchange failed: {token_data}")
                raise HTTPException(status_code=401, detail="Invalid GitHub authorization code.")

            # Fetch user profile
            user_response = httpx.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                timeout=10,
            )
            github_user = user_response.json()

            github_id = str(github_user.get("id"))
            name = github_user.get("name") or github_user.get("login", "GitHub User")
            email = github_user.get("email")

            # If email is not public, fetch from emails endpoint
            if not email:
                emails_response = httpx.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                    timeout=10,
                )
                emails = emails_response.json()
                primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
                if primary:
                    email = primary["email"]

            if not email:
                raise HTTPException(status_code=400, detail="GitHub account has no accessible email. Make your email public on GitHub and try again.")

            logger.info(f"✅ GitHub user verified: {email}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ GitHub token exchange error: {e}")
            raise HTTPException(status_code=401, detail="GitHub authentication failed.")

        user = self.db.upsert_github_user(email, name, github_id)
        logger.info(f"✅ GitHub user upserted: {email} (ID: {user['id']})")

        self._ensure_user_onboarding(user['id'], user['email'])

        token = self.auth_manager.create_access_token(
            data={"sub": str(user["id"]), "email": user["email"], "role": user["role"]}
        )

        return {"access_token": token, "token_type": "bearer", "user": user}

    def _ensure_user_onboarding(self, user_id: int, user_email: str) -> None:
        """Ensure user has required onboarding setup (theia port and project directory)"""
        try:
            logger.info(f"🎯 Ensuring onboarding setup for user {user_id} ({user_email})")
            
            # Step 1: Ensure theia_port is assigned
            if self.theia_manager:
                try:
                    port_assigned = self.theia_manager.ensure_user_port_assigned(user_id)
                    if port_assigned:
                        logger.info(f"✅ Theia port ensured for user {user_id}")
                    else:
                        logger.warning(f"⚠️ Failed to ensure theia port for user {user_id}")
                except Exception as e:
                    logger.error(f"❌ Error ensuring theia_port for user {user_id}: {e}")
            else:
                logger.warning(f"⚠️ Theia manager not available for user {user_id} port assignment")
            
            # Step 2: Ensure project directory exists
            if self.theia_manager:
                try:
                    directory_created = self.theia_manager.ensure_user_project_dir(user_id)
                    if directory_created:
                        logger.info(f"✅ Project directory ensured for user {user_id}")
                    else:
                        logger.warning(f"⚠️ Failed to create project directory for user {user_id}")
                except Exception as e:
                    logger.error(f"❌ Error creating project directory for user {user_id}: {e}")
            else:
                logger.warning(f"⚠️ Theia manager not available for user {user_id} directory creation")
                
        except Exception as e:
            logger.error(f"❌ Error during user onboarding setup for user {user_id}: {e}")
            # Don't fail the authentication due to onboarding issues
            pass
    
    def request_password_reset(self, email: str, background_tasks) -> Dict[str, Any]:
        """
        Request password reset for user
        
        Args:
            email: User's email address
            background_tasks: FastAPI BackgroundTasks for async email sending
            
        Returns:
            Success message (doesn't reveal if user exists for security)
        """
        try:
            user = self.db.get_user_by_email(email)
            
            # Don't reveal if user exists (security best practice)
            if not user:
                logger.info(f"🔐 Password reset requested for non-existent email: {email}")
                return {
                    "message": "If an account with that email exists, a password reset link has been sent."
                }
            
            # Generate password reset token
            token = self.token_service.generate_password_reset_token(email)
            
            # Store token in database with expiry
            expires = datetime.now() + timedelta(hours=1)
            self.db.store_password_reset_token(email, token, expires)
            
            # Build frontend reset URL (frontend handles the token and calls backend)
            reset_url = f"{self.app_public_base_url}/reset-password?token={token}"
            
            # Send email in background
            if background_tasks:
                background_tasks.add_task(
                    self.mail_service.send_password_reset_email,
                    email,
                    reset_url,
                    user['name']
                )
            else:
                # Fallback to synchronous sending
                import asyncio
                asyncio.create_task(self.mail_service.send_password_reset_email(email, reset_url, user['name']))
            
            logger.info(f"✅ Password reset requested for: {email}")
            
            return {
                "message": "If an account with that email exists, a password reset link has been sent."
            }
        except Exception as e:
            logger.error(f"❌ Password reset request failed for {email}: {e}")
            # Don't reveal error details for security
            return {
                "message": "If an account with that email exists, a password reset link has been sent."
            }
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset user password with token
        
        Args:
            token: Password reset token
            new_password: New password to set
            
        Returns:
            Success message
        """
        try:
            # Validate token and get email
            email = self.token_service.validate_password_reset_token(token)
            
            # Also check database token validity
            db_email = self.db.validate_password_reset_token(token)
            
            if not db_email or db_email != email:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid or expired password reset token."
                )
            
            # Validate new password
            if len(new_password) < 8:
                raise HTTPException(
                    status_code=400,
                    detail="Password must be at least 8 characters long."
                )
            
            # Update password
            success = self.db.update_user_password(email, new_password)
            
            if not success:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to update password. Please try again."
                )
            
            logger.info(f"✅ Password reset successful for: {email}")
            
            return {
                "message": "Password has been reset successfully. You can now log in with your new password."
            }
        except ValueError as e:
            # Token validation errors
            logger.warning(f"⚠️ Password reset failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Password reset failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to reset password. Please try again."
            )
    
    def resend_confirmation_email(self, email: str, background_tasks) -> Dict[str, Any]:
        """
        Resend confirmation email to user
        
        Args:
            email: User's email address
            background_tasks: FastAPI BackgroundTasks for async email sending
            
        Returns:
            Success message (doesn't reveal if user exists)
        """
        import time
        try:
            user = self.db.get_user_by_email(email)
            
            # Don't reveal if user exists (security)
            if not user or user.get('is_active'):
                # Add small delay to prevent timing attacks
                time.sleep(0.2)
                logger.info(f"📧 Confirmation resend requested for {email} (no action needed)")
                return {
                    "message": "If your account needs confirmation, an email has been sent."
                }
            
            # Generate new confirmation token
            token = self.token_service.generate_confirmation_token(email)
            confirmation_url = f"{self.app_public_base_url}/verify-email?token={token}"
            
            # Send email in background
            if background_tasks:
                background_tasks.add_task(
                    self.mail_service.send_confirmation_email,
                    email,
                    confirmation_url,
                    user['name']
                )
            
            logger.info(f"✅ Confirmation email resent to: {email}")
            
            return {
                "message": "If your account needs confirmation, an email has been sent."
            }
        except Exception as e:
            logger.error(f"❌ Resend confirmation failed for {email}: {e}")
            # Add small delay to prevent timing attacks
            time.sleep(0.2)
            return {
                "message": "If your account needs confirmation, an email has been sent."
            }
    
    def change_admin_password(self, email: str, current_password: str, new_password: str, confirm_password: str) -> Dict[str, Any]:
        """
        Change admin password
        
        Args:
            email: Admin's email address
            current_password: Current password
            new_password: New password
            confirm_password: Confirmation of new password
            
        Returns:
            Success message
        """
        try:
            # Verify current password
            user = self.db.authenticate_user(email, current_password)
            if not user:
                raise HTTPException(status_code=401, detail="Current password is incorrect")
            
            # Verify user is admin
            if user.get('role') != 'admin':
                raise HTTPException(status_code=403, detail="Admin access required")
            
            # Validate new passwords match
            if new_password != confirm_password:
                raise HTTPException(status_code=400, detail="New passwords do not match")
            
            # Validate new password requirements
            if len(new_password) < 8:
                raise HTTPException(
                    status_code=400,
                    detail="Password must be at least 8 characters long"
                )
            
            # Validate new password is different from current
            if current_password == new_password:
                raise HTTPException(
                    status_code=400,
                    detail="New password must be different from current password"
                )
            
            # Update password
            success = self.db.update_user_password(email, new_password)
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update password. Please try again."
                )
            
            logger.info(f"✅ Admin password changed successfully for: {email}")
            
            return {
                "message": "Password updated successfully"
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Admin password change failed for {email}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to change password. Please try again."
            )
