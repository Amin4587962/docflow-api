# app/schemas.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


# --- Token Schemas ---
class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for data extracted from JWT token payload."""
    user_id: int | None = None


# --- User Schemas ---
class UserBase(BaseModel):
    """Base schema containing common user fields."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration request."""
    password: str


class UserResponse(UserBase):
    """Schema for returning user data (excludes password)."""
    id: int
    created_at: datetime

    # Enable ORM mode to read directly from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)


# --- Document Schemas ---
class DocumentBase(BaseModel):
    """Base schema containing common document metadata."""
    filename: str
    file_size: int
    content_type: str


class DocumentResponse(DocumentBase):
    """Schema for returning document details."""
    id: int
    status: str
    owner_id: int
    created_at: datetime

    # Enable ORM mode to read directly from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)
