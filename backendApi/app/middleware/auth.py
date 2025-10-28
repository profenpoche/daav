"""
Authentication dependencies for FastAPI routes
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.interface.user_interface import User
from app.services.auth_service import AuthService
from app.enums.user_role import UserRole

# Security scheme for JWT Bearer tokens
security = HTTPBearer()

# Initialize auth service
auth_service = AuthService()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials with Bearer token
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
        
    Usage:
        @router.get("/protected")
        async def protected_route(current_user: Annotated[User, Depends(get_current_user)]):
            return {"user": current_user.username}
    """
    token = credentials.credentials
    return await auth_service.get_current_user(token)


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Dependency to require admin role
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Admin user
        
    Raises:
        HTTPException: If user is not admin
        
    Usage:
        @router.post("/admin-only")
        async def admin_route(admin_user: Annotated[User, Depends(require_admin)]):
            return {"message": "Admin access granted"}
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_admin)]
