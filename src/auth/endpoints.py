"""
Authentication endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from auth.models import UserCreate, UserUpdate, UserLogin, UserResponse, User, UserRole, Permission
from auth.auth_service import (
    auth_service, get_current_user, require_permission, require_role,
    AuthenticationError, AuthorizationError
)
from utils.audit_logger import log_security_event, AuditLevel

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def login(user_login: UserLogin, request: Request):
    """User login endpoint"""
    try:
        client_ip = request.client.host if request.client else None
        result = auth_service.authenticate_user(
            username=user_login.username,
            password=user_login.password,
            ip_address=client_ip
        )
        return result
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS))
):
    """Create new user (admin only)"""
    try:
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "password": user_data.password,
            "role": user_data.role.value,
            "department": user_data.department,
            "is_active": True,
            "is_verified": False
        }
        
        user = auth_service.create_user(user_dict, current_user.user_id)
        return UserResponse.from_user(user)
    except (AuthenticationError, AuthorizationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS))
):
    """List all users (admin only)"""
    from database.config import SessionLocal
    from database.repositories import get_user_repo
    
    db = SessionLocal()
    try:
        user_repo = get_user_repo(db)
        db_users = user_repo.get_all_users()
        
        users = []
        for db_user in db_users:
            user = User(
                user_id=str(db_user.user_id),
                username=db_user.username,
                email=db_user.email,
                role=UserRole(db_user.role),
                is_active=db_user.is_active,
                created_at=db_user.created_at,
                last_login=db_user.last_login,
                department=db_user.department
            )
            users.append(UserResponse.from_user(user))
        
        return users
    finally:
        db.close()

@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.from_user(current_user)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user information"""
    try:
        # Users can update themselves, or admins can update anyone
        if user_id != current_user.user_id and not current_user.has_permission(Permission.MANAGE_USERS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        updates = user_data.dict(exclude_unset=True)
        user = auth_service.update_user(user_id, updates, current_user.user_id)
        return UserResponse.from_user(user)
    except (AuthenticationError, AuthorizationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS))
):
    """Delete user (admin only)"""
    try:
        success = auth_service.delete_user(user_id, current_user.user_id)
        return {"message": "User deleted successfully"}
    except (AuthenticationError, AuthorizationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/permissions")
async def get_permissions(current_user: User = Depends(get_current_user)):
    """Get current user's permissions"""
    return {
        "user_id": current_user.user_id,
        "role": current_user.role.value,
        "permissions": [p.value for p in current_user.permissions]
    }

@router.get("/roles")
async def get_roles(current_user: User = Depends(require_permission(Permission.MANAGE_USERS))):
    """Get available roles and their permissions (admin only)"""
    from auth.models import ROLE_PERMISSIONS
    
    roles_info = {}
    for role, permissions in ROLE_PERMISSIONS.items():
        roles_info[role.value] = {
            "name": role.value,
            "permissions": [p.value for p in permissions]
        }
    
    return roles_info
