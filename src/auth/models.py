"""
User authentication and authorization models
"""
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel

class UserRole(Enum):
    """User role definitions with hierarchical permissions"""
    ADMIN = "admin"
    ANALYST = "analyst" 
    VIEWER = "viewer"
    AUDITOR = "auditor"

class Permission(Enum):
    """System permissions"""
    # Document permissions
    UPLOAD_DOCUMENT = "upload_document"
    VIEW_DOCUMENT = "view_document"
    DELETE_DOCUMENT = "delete_document"
    PROCESS_DOCUMENT = "process_document"
    
    # PII permissions
    VIEW_PII = "view_pii"
    EXPORT_PII = "export_pii"
    REDACT_PII = "redact_pii"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    SYSTEM_CONFIG = "system_config"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_REPORTS = "export_reports"
    
    # Customer data permissions
    VIEW_CUSTOMER_DATA = "view_customer_data"
    EDIT_CUSTOMER_DATA = "edit_customer_data"

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.UPLOAD_DOCUMENT,
        Permission.VIEW_DOCUMENT,
        Permission.DELETE_DOCUMENT,
        Permission.PROCESS_DOCUMENT,
        Permission.VIEW_PII,
        Permission.EXPORT_PII,
        Permission.REDACT_PII,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.SYSTEM_CONFIG,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_CUSTOMER_DATA,
        Permission.EDIT_CUSTOMER_DATA,
    ],
    UserRole.ANALYST: [
        Permission.UPLOAD_DOCUMENT,
        Permission.VIEW_DOCUMENT,
        Permission.PROCESS_DOCUMENT,
        Permission.VIEW_PII,
        Permission.REDACT_PII,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_CUSTOMER_DATA,
        Permission.EDIT_CUSTOMER_DATA,
    ],
    UserRole.VIEWER: [
        Permission.VIEW_DOCUMENT,
        Permission.VIEW_CUSTOMER_DATA,
    ],
    UserRole.AUDITOR: [
        Permission.VIEW_DOCUMENT,
        Permission.VIEW_AUDIT_LOGS,
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_CUSTOMER_DATA,
    ]
}

@dataclass
class User:
    """User model"""
    user_id: str
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    department: Optional[str] = None
    supervisor_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
    
    @property
    def permissions(self) -> List[Permission]:
        """Get user permissions based on role"""
        return ROLE_PERMISSIONS.get(self.role, [])
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions
    
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until
    
    def can_access_pii(self) -> bool:
        """Check if user can access PII data"""
        return Permission.VIEW_PII in self.permissions
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users"""
        return Permission.MANAGE_USERS in self.permissions

class UserCreate(BaseModel):
    """Model for creating new users"""
    username: str
    email: str
    password: str
    role: UserRole
    department: Optional[str] = None
    supervisor_id: Optional[str] = None

class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    supervisor_id: Optional[str] = None

class UserLogin(BaseModel):
    """Model for user login"""
    username: str
    password: str

class UserResponse(BaseModel):
    """Model for user response (without sensitive data)"""
    user_id: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    department: Optional[str]
    permissions: List[str]
    
    @classmethod
    def from_user(cls, user: User) -> 'UserResponse':
        return cls(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            department=user.department,
            permissions=[p.value for p in user.permissions]
        )

class AccessLog(BaseModel):
    """Model for access logging"""
    user_id: str
    resource: str
    action: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    details: Optional[Dict[str, Any]] = None
