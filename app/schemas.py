from datetime import datetime
from typing import Any

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
    """Schema for returning user data without password."""
    id: int
    created_at: datetime

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
    task_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    processed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)



class TaskStatusResponse(BaseModel):
    """Schema for returning Celery task status and result."""
    task_id: str
    status: str
    result: Any | None = None

    model_config = ConfigDict(from_attributes=True)
