"""
Token Service - Handles email confirmation token generation and validation
Uses itsdangerous for secure, time-limited tokens
"""

import os
import logging
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TokenService:
    """Service for generating and validating email confirmation tokens"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize TokenService with secret key
        
        Args:
            secret_key: Secret key for token signing (falls back to env variables)
        """
        # Use JWT_SECRET_KEY or SECRET_KEY from environment
        env_secret = os.getenv('JWT_SECRET_KEY') or os.getenv('SECRET_KEY')
        self.secret_key = secret_key or env_secret or 'dev-secret-key'
        
        if self.secret_key == 'dev-secret-key':
            logger.warning("⚠️ Using default secret key for token service. Set JWT_SECRET_KEY or SECRET_KEY in production!")
        
        self.serializer = URLSafeTimedSerializer(self.secret_key)
        self.salt = 'email-confirmation-salt'
        self.max_age = 3600  # 1 hour in seconds
        
        logger.info("✅ Token service initialized")
    
    def generate_confirmation_token(self, email: str) -> str:
        """
        Generate a time-limited confirmation token for an email address
        
        Args:
            email: Email address to generate token for
            
        Returns:
            URL-safe confirmation token string
        """
        try:
            token = self.serializer.dumps(email, salt=self.salt)
            logger.info(f"📧 Generated confirmation token for: {email}")
            return token
        except Exception as e:
            logger.error(f"❌ Failed to generate confirmation token for {email}: {e}")
            raise
    
    def validate_confirmation_token(self, token: str) -> Optional[str]:
        """
        Validate a confirmation token and return the email if valid
        
        Args:
            token: The confirmation token to validate
            
        Returns:
            Email address if token is valid, None if invalid or expired
            
        Raises:
            ValueError: If token is expired (with specific message)
            ValueError: If token is invalid (with specific message)
        """
        try:
            email = self.serializer.loads(
                token,
                salt=self.salt,
                max_age=self.max_age
            )
            logger.info(f"✅ Validated confirmation token for: {email}")
            return email
        except SignatureExpired:
            logger.warning("⚠️ Confirmation token expired")
            raise ValueError("Confirmation token has expired. Please request a new confirmation email.")
        except BadSignature:
            logger.warning("⚠️ Invalid confirmation token signature")
            raise ValueError("Invalid confirmation token. Please check the link or request a new confirmation email.")
        except Exception as e:
            logger.error(f"❌ Token validation error: {e}")
            raise ValueError("Failed to validate confirmation token. Please try again.")
