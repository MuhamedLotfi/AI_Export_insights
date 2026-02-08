"""
Authentication API Router
Handles login, registration, and user management
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Pydantic Models
class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    domain_agents: List[str] = []


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    user = auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login endpoint"""
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    result = auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        user=UserResponse(
            id=result["id"],
            username=result["username"],
            email=result.get("email", ""),
            role=result.get("role", "user"),
            domain_agents=result.get("domain_agents", [])
        )
    )


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """User registration endpoint"""
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    result = auth_service.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    return UserResponse(
        id=result["id"],
        username=result["username"],
        email=result.get("email", ""),
        role=result.get("role", "user"),
        domain_agents=[]
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    user_agents = auth_service.get_user_domain_agents(current_user["id"])
    
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user.get("email", ""),
        role=current_user.get("role", "user"),
        domain_agents=user_agents
    )


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    """Get all users (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    users = auth_service.get_all_users()
    
    return [
        UserResponse(
            id=u["id"],
            username=u["username"],
            email=u.get("email", ""),
            role=u.get("role", "user"),
            domain_agents=auth_service.get_user_domain_agents(u["id"])
        )
        for u in users
    ]


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user (admin or self)"""
    if current_user.get("role") != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    update_data = user_data.dict(exclude_unset=True)
    
    result = auth_service.update_user(user_id, update_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=result["id"],
        username=result["username"],
        email=result.get("email", ""),
        role=result.get("role", "user"),
        domain_agents=auth_service.get_user_domain_agents(result["id"])
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete user (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    success = auth_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


class PasswordReset(BaseModel):
    new_password: str


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    password_data: PasswordReset,
    current_user: dict = Depends(get_current_user)
):
    """Reset user password (admin or self)"""
    if current_user.get("role") != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reset this user's password"
        )
    
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    success = auth_service.reset_password(user_id, password_data.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password reset successfully"}


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint (token invalidation would require token blacklist)"""
    return {"message": "Logged out successfully"}
