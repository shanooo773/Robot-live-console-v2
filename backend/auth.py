import jwt
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib

security = HTTPBearer()

class AuthManager:
    def __init__(self, secret_key: Optional[str] = None):
        # Use environment variable for secret key, fallback to provided key, or generate random
        env_secret = os.getenv('JWT_SECRET_KEY')
        self.secret_key = env_secret or secret_key or secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.access_token_expire_hours = 24
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=self.access_token_expire_hours)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Get current user from JWT token"""
        token = credentials.credentials
        payload = self.verify_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    def require_admin(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Require admin role with enhanced privilege validation and audit logging"""
        import logging
        logger = logging.getLogger(__name__)
        
        user_id = current_user.get("sub")
        user_email = current_user.get("email", "unknown")
        user_role = current_user.get("role")
        
        # Log admin access attempt for audit trail
        logger.info(f"🔐 ADMIN ACCESS ATTEMPT - User {user_id} ({user_email}) with role '{user_role}' attempting admin access")
        
        # Check if user has admin role
        if user_role != "admin":
            logger.warning(f"❌ ADMIN ACCESS DENIED - User {user_id} ({user_email}) with role '{user_role}' denied admin access")
            raise HTTPException(
                status_code=403,
                detail="Admin access required. Only administrators can access this resource."
            )
        
        # Additional validation for demo admin accounts
        # Demo admins should have full access but we log it separately
        is_demo_admin = any(demo_indicator in user_email.lower() for demo_indicator in ['demo', 'test'])
        if is_demo_admin:
            logger.info(f"🎯 DEMO ADMIN ACCESS - Demo admin {user_id} ({user_email}) granted access")
        else:
            logger.info(f"✅ ADMIN ACCESS GRANTED - Real admin {user_id} ({user_email}) granted access")
        
        return current_user

# Global auth manager instance
# Use a test-friendly secret key if in testing environment
auth_manager = AuthManager()

# Dependency functions for FastAPI
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    return auth_manager.get_current_user(credentials)

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role"""
    return auth_manager.require_admin(current_user)