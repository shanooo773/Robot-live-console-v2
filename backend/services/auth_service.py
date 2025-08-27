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

logger = logging.getLogger(__name__)

class AuthServiceException(Exception):
    """Exception raised when authentication service encounters an error"""
    pass

class AuthService:
    """
    Service for handling user authentication and authorization.
    This service operates independently of Docker and other services.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.auth_manager = auth_manager
        self.available = True
        self.status = "available"
        
        # Load demo credentials from environment variables
        self.demo_user_email = os.getenv("DEMO_USER_EMAIL", "demo@user.com")
        self.demo_user_password = os.getenv("DEMO_USER_PASSWORD", "password")
        self.demo_admin_email = os.getenv("DEMO_ADMIN_EMAIL", "admin@demo.com")
        self.demo_admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "password")
        
        logger.info("✅ Auth service initialized successfully")
        logger.info(f"🎯 Demo user email: {self.demo_user_email}")
        logger.info(f"👑 Demo admin email: {self.demo_admin_email}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": "auth",
            "available": self.available,
            "status": self.status,
            "features": ["registration", "login", "jwt_tokens", "role_management"]
        }
    
    def _check_demo_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Check if credentials match demo user accounts"""
        if email == self.demo_user_email and password == self.demo_user_password:
            return {
                "id": -1,  # Use negative ID for demo users to avoid conflicts
                "name": "Demo User",
                "email": self.demo_user_email,
                "role": "user",
                "isDemoUser": True,
                "created_at": "2024-01-01T00:00:00"
            }
        elif email == self.demo_admin_email and password == self.demo_admin_password:
            return {
                "id": -2,  # Use negative ID for demo admin to avoid conflicts
                "name": "Demo Admin", 
                "email": self.demo_admin_email,
                "role": "admin",
                "isDemoAdmin": True,
                "created_at": "2024-01-01T00:00:00"
            }
        return None
    
    def register_user(self, name: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user"""
        try:
            logger.info(f"📝 Registration attempt for email: {email}")
            user = self.db.create_user(name, email, password)
            logger.info(f"✅ User registered successfully: {email} (ID: {user['id']})")
            
            token = self.auth_manager.create_access_token(
                data={"sub": str(user["id"]), "email": user["email"], "role": user["role"]}
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": user
            }
        except ValueError as e:
            logger.warning(f"⚠️ Registration failed for {email}: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"❌ Registration failed with exception for {email}: {e}")
            raise AuthServiceException(f"Registration failed: {str(e)}")
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and return token"""
        try:
            logger.info(f"🔐 Login attempt for email: {email}")
            
            # First check if this is a demo user
            demo_user = self._check_demo_user(email, password)
            if demo_user:
                # Create token data with demo user flags
                token_data = {
                    "sub": str(demo_user["id"]),
                    "email": demo_user["email"],
                    "role": demo_user["role"]
                }
                
                # Add demo flags to token data
                if demo_user.get("isDemoUser"):
                    token_data["isDemoUser"] = True
                if demo_user.get("isDemoAdmin"):
                    token_data["isDemoAdmin"] = True
                
                token = self.auth_manager.create_access_token(data=token_data)
                
                logger.info(f"🎯 Demo user login successful: {email} with role {demo_user['role']}")
                return {
                    "access_token": token,
                    "token_type": "bearer",
                    "user": demo_user
                }
            
            # Otherwise, authenticate against database
            logger.info(f"📊 Checking database authentication for: {email}")
            user = self.db.authenticate_user(email, password)
            if not user:
                logger.warning(f"❌ Database authentication failed for: {email}")
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            logger.info(f"✅ Database authentication successful for: {email} (ID: {user['id']}, Role: {user['role']})")
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