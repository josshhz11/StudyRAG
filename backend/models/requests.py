"""Pydantic models for API requests"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class SignUpRequest(BaseModel):
    """User signup request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=50)

class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str

class ChatRequest(BaseModel):
    """Chat query request"""
    query: str = Field(..., min_length=1)
    active_semester: Optional[str] = None
    active_subject: Optional[str] = None
    active_books: list[str] = []

class UploadMetadata(BaseModel):
    """File upload metadata"""
    semester: str
    subject: str
    book_id: str
