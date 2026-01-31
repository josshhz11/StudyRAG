"""
Authentication router - signup, login, logout, profile
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from core.dependencies import get_supabase_client, get_current_user
from models.requests import SignUpRequest, LoginRequest
from models.responses import AuthResponse, UserResponse, MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Register a new user.
    
    - Creates user in Supabase auth
    - Auto-creates profile via database trigger
    - Returns user info and access token
    """
    try:
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "username": request.username
                }
            }
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signup failed. User not created."
            )
        
        return AuthResponse(
            user=UserResponse(
                user_id=response.user.id,
                email=response.user.email,
                username=request.username
            ),
            access_token=response.session.access_token if response.session else "",
            refresh_token=response.session.refresh_token if response.session else None,
            expires_at=response.session.expires_at if response.session else None
        )
    
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {error_msg}"
        )

@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Login user with email and password.
    
    Returns access token and user info.
    """
    try:
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Get username from user metadata or profile
        username = None
        if response.user.user_metadata:
            username = response.user.user_metadata.get('username')
        
        return AuthResponse(
            user=UserResponse(
                user_id=response.user.id,
                email=response.user.email,
                username=username
            ),
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_at=response.session.expires_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout", response_model=MessageResponse)
async def logout(
    user_id: str = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Logout current user (invalidate session).
    """
    try:
        supabase.auth.sign_out()
        return MessageResponse(message="Logged out successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user_id: str = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get current authenticated user's profile.
    """
    try:
        # Get user from auth
        user = supabase.auth.get_user()
        
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get profile from database
        profile = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        username = None
        if profile.data and len(profile.data) > 0:
            username = profile.data[0].get('username')
        elif user.user.user_metadata:
            username = user.user.user_metadata.get('username')
        
        return UserResponse(
            user_id=user.user.id,
            email=user.user.email,
            username=username,
            created_at=user.user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )
