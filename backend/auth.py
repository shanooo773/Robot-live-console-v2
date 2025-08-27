import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib

security = HTTPBearer()

class AuthManager:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
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
        """Require admin role"""
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        return current_user

# Global auth manager instance
auth_manager = AuthManager()

# Dependency functions for FastAPI
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    return auth_manager.get_current_user(credentials)

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role"""
    return auth_manager.require_admin(current_user)