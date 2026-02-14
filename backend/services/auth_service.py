"""
Authentication Service - Handles user authentication and authorization
This service is completely independent of Docker and should always be available.
"""

import logging
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException
from auth import auth_manager
from database import DatabaseManager
from services.token_service import TokenService
from services.mail_service import MailService

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
        self.mail_service = MailService()
        
        # Get server host for confirmation URLs
        self.server_host = os.getenv("SERVER_HOST", "http://localhost:8000")
        
        logger.info("✅ Auth service initialized successfully")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": "auth",
            "available": self.available,
            "status": self.status,
            "features": ["registration", "login", "jwt_tokens", "role_management", "email_confirmation", "google_oauth", "password_reset"]
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
            
            # Build confirmation URL
            confirmation_url = f"{self.server_host}/auth/confirm?token={token}"
            
            # Send email asynchronously
            await self.mail_service.send_confirmation_email(email, confirmation_url, name)
            
            return confirmation_url
        except Exception as e:
            logger.error(f"❌ Failed to send confirmation email for {email}: {e}")
            raise
    
    async def register_user(self, name: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user and send confirmation email (no immediate JWT)"""
        try:
            logger.info(f"📝 Registration attempt for email: {email}")
            user = self.db.create_user(name, email, password)
            logger.info(f"✅ User registered successfully: {email} (ID: {user['id']})")
            
            # Send confirmation email (async)
            confirmation_url = await self.send_confirmation_email(user['email'], user['name'])
            
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
                idinfo = google_id_token.verify_oauth2_token(
                    id_token, 
                    requests.Request(), 
                    google_client_id
                )
                
                # Extract user information from Google token
                google_user_id = idinfo['sub']
                email = idinfo.get('email')
                
                if not email:
                    raise HTTPException(status_code=400, detail="Email not provided by Google")
                
                # Check if email is verified
                email_verified = idinfo.get("email_verified")
                if email_verified is not True:
                    logger.warning(f"⚠️ Google account email not verified for: {email}")
                    raise HTTPException(
                        status_code=401,
                        detail="Google account email is not verified"
                    )
                
                name = idinfo.get('name', email.split('@')[0])
                
                logger.info(f"✅ Google token verified for: {email}")
                
            except ValueError as e:
                logger.warning(f"⚠️ Invalid Google token: {e}")
                raise HTTPException(status_code=401, detail="Invalid Google token")
            
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
    
    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request a password reset for a user
        
        Args:
            email: User's email address
            
        Returns:
            Success message and reset URL (for dev/testing)
        """
        try:
            # Check if user exists
            user = self.db.get_user_by_email(email)
            if not user:
                # Don't reveal if user exists or not for security
                logger.info(f"🔑 Password reset requested")
                return {
                    "message": "If an account exists with that email, a password reset link has been sent."
                }
            
            # Generate reset token
            token = self.token_service.generate_password_reset_token(email)
            
            # Build reset URL
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            reset_url = f"{frontend_url}/reset-password?token={token}"
            
            # Send email asynchronously
            await self.mail_service.send_password_reset_email(email, reset_url, user['name'])
            
            logger.info(f"✅ Password reset email sent")
            
            return {
                "message": "If an account exists with that email, a password reset link has been sent.",
                "reset_url": reset_url  # Include for dev/testing
            }
        except Exception as e:
            logger.error(f"❌ Failed to send password reset: {e}")
            # Return generic message even on error to not reveal user existence
            return {
                "message": "If an account exists with that email, a password reset link has been sent."
            }
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset user password with token
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            Success message
        """
        try:
            # Validate token and get email
            email = self.token_service.validate_password_reset_token(token)
            
            # Update password
            success = self.db.update_user_password(email, new_password)
            
            if not success:
                raise HTTPException(status_code=404, detail="User not found")
            
            logger.info(f"✅ Password reset successful for: {email}")
            
            return {
                "message": "Password has been reset successfully. You can now log in with your new password."
            }
        except ValueError as e:
            # Token validation errors (expired, invalid)
            logger.warning(f"⚠️ Password reset failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Password reset failed with exception: {e}")
            raise AuthServiceException(f"Password reset failed: {str(e)}")
    
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