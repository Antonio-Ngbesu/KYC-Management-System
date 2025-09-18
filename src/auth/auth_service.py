"""
Authentication and authorization middleware
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth.models import User, UserRole, Permission, AccessLog
from auth.jwt_service import jwt_manager
from database.config import SessionLocal
from database.repositories import get_user_repo
from utils.audit_logger import log_security_event, AuditLevel

class AuthenticationError(Exception):
    """Authentication related errors"""
    pass

class AuthorizationError(Exception):
    """Authorization related errors"""
    pass

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Will be closed by caller

class AuthService:
    """Authentication and authorization service with database integration"""
    
    def authenticate_user(self, username: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        """Authenticate user and return token"""
        db = get_db()
        
        try:
            user_repo = get_user_repo(db)
            
            # Find user by username
            db_user = user_repo.get_user_by_username(username)
            
            if not db_user:
                log_security_event(
                    event_type="login_failed",
                    description=f"Login attempt with invalid username: {username}",
                    severity=AuditLevel.WARNING,
                    ip_address=ip_address
                )
                raise AuthenticationError("Invalid credentials")
            
            # Convert DB user to auth model
            user = User(
                user_id=str(db_user.user_id),
                username=db_user.username,
                email=db_user.email,
                role=UserRole(db_user.role),
                is_active=db_user.is_active,
                created_at=db_user.created_at,
                last_login=db_user.last_login,
                failed_login_attempts=db_user.failed_login_attempts or 0,
                locked_until=db_user.locked_until,
                department=db_user.department
            )
            
            # Check if account is locked
            if user.is_locked():
                log_security_event(
                    event_type="login_blocked",
                    description=f"Login attempt on locked account: {username}",
                    severity=AuditLevel.WARNING,
                    user_id=user.user_id,
                    ip_address=ip_address
                )
                raise AuthenticationError("Account is locked")
            
            # Check if account is active
            if not user.is_active:
                log_security_event(
                    event_type="login_blocked",
                    description=f"Login attempt on inactive account: {username}",
                    severity=AuditLevel.WARNING,
                    user_id=user.user_id,
                    ip_address=ip_address
                )
                raise AuthenticationError("Account is inactive")
            
            # Verify password
            if not jwt_manager.verify_password(password, db_user.password_hash):
                # Increment failed attempts
                user_repo.increment_failed_login_attempts(str(db_user.user_id))
                
                # Check if should lock account
                if (db_user.failed_login_attempts or 0) + 1 >= 5:
                    lock_until = datetime.now(timezone.utc) + timedelta(hours=1)
                    user_repo.lock_user(str(db_user.user_id), lock_until)
                    
                    log_security_event(
                        event_type="account_locked",
                        description=f"Account locked due to failed login attempts: {username}",
                        severity=AuditLevel.WARNING,
                        user_id=user.user_id,
                        ip_address=ip_address
                    )
                
                log_security_event(
                    event_type="login_failed",
                    description=f"Invalid password for user: {username}",
                    severity=AuditLevel.WARNING,
                    user_id=user.user_id,
                    ip_address=ip_address
                )
                raise AuthenticationError("Invalid credentials")
            
            # Reset failed attempts and update last login
            user_repo.reset_failed_login_attempts(str(db_user.user_id))
            user_repo.update_last_login(str(db_user.user_id))
            
            # Create token pair
            token_data = jwt_manager.create_token_pair(user)
            
            log_security_event(
                event_type="login_success",
                description=f"Successful login: {username}",
                severity=AuditLevel.INFO,
                user_id=user.user_id,
                ip_address=ip_address
            )
            
            return token_data
            
        finally:
            db.close()
    
    def verify_token(self, token: str) -> User:
        """Verify JWT token and return user"""
        try:
            user_data = jwt_manager.get_user_from_token(token)
            
            db = get_db()
            try:
                user_repo = get_user_repo(db)
                db_user = user_repo.get_user_by_id(user_data["user_id"])
                
                if not db_user or not db_user.is_active:
                    raise AuthenticationError("User not found or inactive")
                
                # Convert to auth model
                user = User(
                    user_id=str(db_user.user_id),
                    username=db_user.username,
                    email=db_user.email,
                    role=UserRole(db_user.role),
                    is_active=db_user.is_active,
                    created_at=db_user.created_at,
                    last_login=db_user.last_login,
                    failed_login_attempts=db_user.failed_login_attempts or 0,
                    locked_until=db_user.locked_until,
                    department=db_user.department
                )
                
                return user
                
            finally:
                db.close()
                
        except Exception as e:
            raise AuthenticationError(f"Token verification failed: {str(e)}")
    
    def create_user(self, user_data: Dict[str, Any], creator_user_id: str) -> User:
        """Create new user"""
        db = get_db()
        
        try:
            user_repo = get_user_repo(db)
            
            # Check if creator has permission
            creator_db = user_repo.get_user_by_id(creator_user_id)
            if not creator_db:
                raise AuthorizationError("Creator not found")
            
            creator_user = User(
                user_id=str(creator_db.user_id),
                username=creator_db.username,
                email=creator_db.email,
                role=UserRole(creator_db.role),
                is_active=creator_db.is_active,
                created_at=creator_db.created_at,
                department=creator_db.department
            )
            
            if not creator_user.has_permission(Permission.MANAGE_USERS):
                raise AuthorizationError("Insufficient permissions to create users")
            
            # Hash password
            if 'password' in user_data:
                user_data['password_hash'] = jwt_manager.hash_password(user_data.pop('password'))
            
            # Create user in database
            db_user = user_repo.create_user(user_data)
            
            # Convert to auth model
            user = User(
                user_id=str(db_user.user_id),
                username=db_user.username,
                email=db_user.email,
                role=UserRole(db_user.role),
                is_active=db_user.is_active,
                created_at=db_user.created_at,
                department=db_user.department
            )
            
            log_security_event(
                event_type="user_created",
                description=f"New user created: {user.username} with role {user.role.value}",
                severity=AuditLevel.INFO,
                user_id=creator_user_id,
                additional_details={"new_user_id": user.user_id, "role": user.role.value}
            )
            
            return user
            
        finally:
            db.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        db = get_db()
        
        try:
            user_repo = get_user_repo(db)
            db_user = user_repo.get_user_by_id(user_id)
            
            if not db_user:
                return None
            
            return User(
                user_id=str(db_user.user_id),
                username=db_user.username,
                email=db_user.email,
                role=UserRole(db_user.role),
                is_active=db_user.is_active,
                created_at=db_user.created_at,
                last_login=db_user.last_login,
                failed_login_attempts=db_user.failed_login_attempts or 0,
                locked_until=db_user.locked_until,
                department=db_user.department
            )
            
        finally:
            db.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        db = get_db()
        
        try:
            user_repo = get_user_repo(db)
            db_user = user_repo.get_user_by_username(username)
            
            if not db_user:
                return None
            
            return User(
                user_id=str(db_user.user_id),
                username=db_user.username,
                email=db_user.email,
                role=UserRole(db_user.role),
                is_active=db_user.is_active,
                created_at=db_user.created_at,
                last_login=db_user.last_login,
                failed_login_attempts=db_user.failed_login_attempts or 0,
                locked_until=db_user.locked_until,
                department=db_user.department
            )
            
        finally:
            db.close()
    
    def check_permission(self, user: User, permission: Permission, resource: str = None) -> bool:
        """Check if user has permission for specific resource"""
        
        if not user.is_active:
            return False
        
        # Check basic permission
        if not user.has_permission(permission):
            log_security_event(
                event_type="permission_denied",
                description=f"Permission denied: {user.username} attempted {permission.value}",
                severity=AuditLevel.WARNING,
                user_id=user.user_id,
                additional_details={"permission": permission.value, "resource": resource}
            )
            return False
        
        return True

# Global auth service instance
auth_service = AuthService()

# FastAPI dependencies
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user"""
    try:
        user = auth_service.verify_token(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))

def require_permission(permission: Permission):
    """Dependency factory to require specific permission"""
    def permission_checker(user: User = Depends(get_current_user)) -> User:
        if not auth_service.check_permission(user, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return user
    return permission_checker

def require_role(role: UserRole):
    """Dependency factory to require specific role"""
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {role.value}"
            )
        return user
    return role_checker

# Convenience functions
def get_user_from_request(request: Request) -> Optional[User]:
    """Extract user from request if authenticated"""
    try:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            return auth_service.verify_token(token)
    except:
        pass
    return None
