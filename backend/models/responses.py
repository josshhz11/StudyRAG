"""Pydantic models for API responses"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserResponse(BaseModel):
    """User information response"""
    user_id: str
    email: str
    username: Optional[str] = None
    created_at: Optional[datetime] = None

class AuthResponse(BaseModel):
    """Authentication response"""
    user: UserResponse
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    success: bool = False

class ChatResponse(BaseModel):
    """Chat query response"""
    answer: str
    sources: List[Dict[str, Any]] = []

class FileInfo(BaseModel):
    """File information"""
    key: str
    semester: str
    subject: str
    book_id: str
    book_title: str
    size: int
    s3_url: Optional[str] = None

class FilesResponse(BaseModel):
    """List of files response"""
    files: List[FileInfo]
    total: int
