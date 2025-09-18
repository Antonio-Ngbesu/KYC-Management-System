"""
Pydantic models for customer management API
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum

from database.models import KYCStatus, RiskLevel


class CustomerBase(BaseModel):
    """Base customer model"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    address_line_1: Optional[str] = Field(None, max_length=200)
    address_line_2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    nationality: Optional[str] = Field(None, max_length=100)


class CustomerCreate(CustomerBase):
    """Customer creation model"""
    kyc_status: Optional[KYCStatus] = KYCStatus.PENDING
    risk_level: Optional[RiskLevel] = RiskLevel.MEDIUM
    notes: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, hyphens, parentheses, and plus sign')
        return v


class CustomerUpdate(BaseModel):
    """Customer update model"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    address_line_1: Optional[str] = Field(None, max_length=200)
    address_line_2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    nationality: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    notes: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, hyphens, parentheses, and plus sign')
        return v


class CustomerResponse(CustomerBase):
    """Customer response model"""
    customer_id: str
    kyc_status: KYCStatus
    risk_level: RiskLevel
    kyc_status_updated_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class CustomerSearch(BaseModel):
    """Customer search model"""
    query: Optional[str] = Field(None, description="Search query for name, email, or phone")
    kyc_status: Optional[List[KYCStatus]] = Field(None, description="Filter by KYC status")
    risk_level: Optional[List[RiskLevel]] = Field(None, description="Filter by risk level")
    country: Optional[str] = Field(None, description="Filter by country")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date (after)")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date (before)")
    limit: Optional[int] = Field(50, ge=1, le=1000, description="Maximum number of results")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")


class KYCStatusUpdate(BaseModel):
    """KYC status update model"""
    status: KYCStatus
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes about the status change")


class CustomerStatistics(BaseModel):
    """Customer statistics model"""
    total_customers: int
    active_customers: int
    inactive_customers: int
    kyc_status_breakdown: dict
    risk_level_breakdown: dict
    recent_registrations: int  # Last 30 days
    pending_kyc_count: int
    approved_kyc_count: int
    rejected_kyc_count: int


class DocumentSummary(BaseModel):
    """Document summary model for customer details"""
    document_id: str
    document_type: str
    file_name: str
    file_size: int
    mime_type: str
    upload_status: str
    processing_status: str
    created_at: datetime
    updated_at: datetime


class KYCSessionSummary(BaseModel):
    """KYC session summary model"""
    session_id: str
    customer_id: str
    status: str
    risk_score: Optional[float] = None
    completion_percentage: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class CustomerDetailResponse(CustomerResponse):
    """Detailed customer response with related data"""
    documents: List[DocumentSummary] = []
    kyc_sessions: List[KYCSessionSummary] = []
    total_documents: int = 0
    latest_session: Optional[KYCSessionSummary] = None


class CustomerListResponse(BaseModel):
    """Paginated customer list response"""
    customers: List[CustomerResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
