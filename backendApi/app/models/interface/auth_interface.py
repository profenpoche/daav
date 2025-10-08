from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token to get new access token")


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @property
    def validate_new_password(self):
        """Validate new password complexity"""
        if len(self.new_password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in self.new_password):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in self.new_password):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in self.new_password):
            raise ValueError('Password must contain at least one special character')
        return True


class ShareResourceRequest(BaseModel):
    """Share resource (dataset or workflow) with another user"""
    resource_id: str = Field(..., description="ID of the resource to share")
    target_user_id: str = Field(..., description="ID of the user to share with")
    resource_type: str = Field(..., pattern="^(dataset|workflow)$", description="Type of resource: dataset or workflow")


class UnshareResourceRequest(BaseModel):
    """Unshare resource from another user"""
    resource_id: str = Field(..., description="ID of the resource to unshare")
    target_user_id: str = Field(..., description="ID of the user to unshare from")
    resource_type: str = Field(..., pattern="^(dataset|workflow)$", description="Type of resource: dataset or workflow")


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema"""
    email: EmailStr = Field(..., description="Email address to send password reset link")


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
