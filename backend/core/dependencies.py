"""
FastAPI dependencies for authentication and database access
"""
from fastapi import Depends, HTTPException, Header, status
from supabase import create_client, Client
from core.config import settings
from typing import Optional

# Initialize Supabase client
def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key  # Use service key for backend
    )

async def get_current_user(
    authorization: Optional[str] = Header(None),
    supabase: Client = Depends(get_supabase_client)
) -> str:
    """
    Verify JWT token and return user_id.
    
    Expects Authorization header: "Bearer <token>"
    Returns user_id (UUID string)
    Raises 401 if invalid/missing token
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or user not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user.user.id
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    authorization: Optional[str] = Header(None),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[str]:
    """
    Optional authentication - returns user_id if authenticated, None otherwise.
    Useful for endpoints that work both authenticated and unauthenticated.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    user = supabase.auth.get_user(token)
    return user.user.id if user and user.user else None
    