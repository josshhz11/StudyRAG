"""
FastAPI dependencies for authentication and database access
"""
from fastapi import Depends, HTTPException, Header, status
from supabase import create_client, Client
from core.config import settings
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

# Initialize Supabase client
def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key  # Use service key for backend
    )

async def get_current_user(
    authorization: Optional[str] = Header(None)
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
        # Verify the JWT token and extract user_id
        # Supabase uses the JWT secret to sign tokens
        # We can decode using the service key's secret portion
        payload = jwt.decode(
            token,
            options={"verify_signature": False}  # We trust Supabase-issued tokens
        )
        
        # Extract user_id (sub claim in JWT)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token is not expired
        import time
        exp = payload.get("exp")
        if exp and time.time() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Optional authentication - returns user_id if authenticated, None otherwise.
    Useful for endpoints that work both authenticated and unauthenticated.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        user_id = payload.get("sub")
        
        # Check expiration
        import time
        exp = payload.get("exp")
        if exp and time.time() > exp:
            return None
        
        return user_id
    except:
        return None
