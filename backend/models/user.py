"""
User Models for Authentication System
Pydantic models for user data and authentication
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
import uuid

class UserRole(str, Enum):
    """User roles for authorization"""
    ADMIN = "admin"
    EDITOR = "editor"  
    VIEWER = "viewer"
    API_USER = "api_user"

class UserStatus(str, Enum):
    """User status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class TokenType(str, Enum):
    """JWT token types"""
    ACCESS = "access"
    REFRESH = "refresh"

class Token(BaseModel):
    """JWT Token model"""
    token_type: str = Field(default="bearer")
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int  # seconds
    expires_at: datetime

class TokenPayload(BaseModel):
    """JWT Token payload"""
    sub: str  # user ID
    email: str
    role: UserRole
    token_type: TokenType
    iat: datetime
    exp: datetime  # expiry
    jti: str  # token ID for blacklisting

class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = Field(default=UserRole.VIEWER)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    last_login: Optional[datetime] = None
    login_count: int = Field(default=0)
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None

class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., description="Password confirmation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@example.com",
                "username": "admin",
                "first_name": "Admin",
                "last_name": "User", 
                "password": "SecurePassword123!",
                "confirm_password": "SecurePassword123!",
                "role": "admin"
            }
        }

class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str
    remember_me: bool = Field(default=False, description="Extend session duration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "SecurePassword123!",
                "remember_me": False
            }
        }

class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    current_password: str = Field(..., description="Required for password changes")
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)
    confirm_new_password: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "newemail@example.com",
                "first_name": "Updated",
                "last_name": "Name",
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword123!",
                "confirm_new_password": "NewSecurePassword123!"
            }
        }

class UserPasswordReset(BaseModel):
    """Password reset request model"""
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

class UserPasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., description="Password confirmation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "NewSecurePassword123!",
                "confirm_password": "NewSecurePassword123!"
            }
        }

class UserResponse(BaseModel):
    """User response model (excludes sensitive data)"""
    id: str
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole
    status: UserStatus
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    login_count: int
    created_at: datetime
    updated_at: datetime
    profile_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "admin@example.com",
                "username": "admin",
                "first_name": "Admin",
                "last_name": "User",
                "role": "admin",
                "status": "active",
                "is_active": True,
                "last_login": "2025-10-30T13:25:00Z",
                "login_count": 42,
                "created_at": "2025-10-01T10:00:00Z",
                "updated_at": "2025-10-30T13:25:00Z",
                "profile_image_url": None
            }
        }

class UserListResponse(BaseModel):
    """User list response with pagination"""
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int

class AuthResponse(BaseModel):
    """Authentication response model"""
    success: bool
    message: str
    data: Optional[dict] = None
    
    # Token data
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    
    # User data
    user: Optional[UserResponse] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Login successful",
                "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "admin@example.com",
                    "username": "admin",
                    "first_name": "Admin",
                    "last_name": "User",
                    "role": "admin",
                    "status": "active",
                    "is_active": True,
                    "last_login": "2025-10-30T13:25:00Z",
                    "login_count": 42,
                    "created_at": "2025-10-01T10:00:00Z",
                    "updated_at": "2025-10-30T13:25:00Z"
                }
            }
        }

class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    user_id: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    is_active: bool = True

# Utility functions for User ID generation
def generate_user_id() -> str:
    """Generate unique user ID"""
    return str(uuid.uuid4())

def generate_session_id() -> str:
    """Generate unique session ID"""
    return str(uuid.uuid4())

def generate_jti() -> str:
    """Generate unique JWT token ID for blacklisting"""
    return str(uuid.uuid4())
