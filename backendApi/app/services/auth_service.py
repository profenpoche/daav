import logging
from datetime import datetime
from typing import Optional, Tuple
from fastapi import HTTPException, status

from app.models.interface.user_interface import User
from app.models.interface.auth_interface import Token, TokenData
from app.utils.auth_utils import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.services.user_service import UserService
from app.utils.singleton import SingletonMeta

logger = logging.getLogger(__name__)


class AuthService(metaclass=SingletonMeta):
    """Service for authentication operations"""
    
    def __init__(self):
        self.user_service = UserService()
        logger.info("AuthService initialized")
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username/email and password
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User: Authenticated user or None
        """
        try:
            # Find user by username or email
            user = await self.user_service.get_user_by_username_or_email(username)
            
            if not user:
                logger.warning(f"Authentication failed: User not found - {username}")
                return None
            
            # Check if account is active
            if not user.is_active:
                logger.warning(f"Authentication failed: Account inactive - {username}")
                return None
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: Invalid password - {username}")
                return None
            
            logger.info(f"User authenticated successfully: {user.username}")
            return user
        
        except Exception as e:
            logger.error(f"Error during authentication: {e}", exc_info=True)
            return None
    
    async def login(self, username: str, password: str) -> Token:
        """
        Login user and return JWT tokens
        
        Args:
            username: Username or email
            password: Password
            
        Returns:
            Token: Access and refresh tokens
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Authenticate user
            user = await self.authenticate_user(username, password)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update last login
            await self.user_service.update_last_login(user.id)
            
            # Create tokens
            token_data = {
                "sub": user.id,
                "username": user.username,
                "role": user.role.value
            }
            
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            
            logger.info(f"Login successful: {user.username}")
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during login: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )
    
    async def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Generate new access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Token: New access and refresh tokens
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        try:
            # Verify it's a refresh token
            verify_token_type(refresh_token, "refresh")
            
            # Decode token
            token_data = decode_token(refresh_token)
            
            # Get user
            user = await self.user_service.get_user_by_id(token_data.user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create new tokens
            new_token_data = {
                "sub": user.id,
                "username": user.username,
                "role": user.role.value
            }
            
            new_access_token = create_access_token(new_token_data)
            new_refresh_token = create_refresh_token(new_token_data)
            
            logger.info(f"Token refreshed for user: {user.username}")
            
            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer"
            )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_current_user(self, token: str) -> User:
        """
        Get current user from access token
        
        Args:
            token: JWT access token
            
        Returns:
            User: Current authenticated user
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        try:
            # Verify it's an access token
            verify_token_type(token, "access")
            
            # Decode token
            token_data = decode_token(token)
            
            # Get user
            user = await self.user_service.get_user_by_id(token_data.user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting current user: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def verify_admin(self, user: User) -> bool:
        """
        Verify if user is admin
        
        Args:
            user: User to verify
            
        Returns:
            bool: True if user is admin
            
        Raises:
            HTTPException: If user is not admin
        """
        from app.enums.user_role import UserRole
        
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return True
