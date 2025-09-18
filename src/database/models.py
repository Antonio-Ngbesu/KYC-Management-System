"""
Database models for KYC Document Analyzer
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, Float, 
    ForeignKey, Enum as SQLEnum, JSON, LargeBinary, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum

from database.config import Base
from models.kyc_models import DocumentType, DocumentStatus, KYCStatus
from auth.models import UserRole


class CustomerStatus(enum.Enum):
    """Customer status in KYC process"""
    REGISTERED = "registered"
    PENDING_VERIFICATION = "pending_verification"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class RiskLevel(enum.Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkflowStatus(enum.Enum):
    """KYC workflow status"""
    INITIALIZED = "initialized"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADDITIONAL_INFO_REQUIRED = "additional_info_required"


# Customer Models
class Customer(Base):
    """Customer information"""
    __tablename__ = "customers"

    customer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_customer_id = Column(String(100), unique=True, nullable=True, index=True)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    nationality = Column(String(50), nullable=True)
    gender = Column(String(10), nullable=True)
    
    # Contact Information
    email = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # KYC Information
    kyc_status = Column(SQLEnum(KYCStatus), default=KYCStatus.PENDING, nullable=False)
    customer_status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.REGISTERED, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM, nullable=False)
    risk_score = Column(Float, default=0.0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    kyc_completed_at = Column(DateTime, nullable=True)
    last_reviewed_at = Column(DateTime, nullable=True)
    
    # Metadata
    source_application = Column(String(100), nullable=True)
    referral_code = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="customer", cascade="all, delete-orphan")
    kyc_sessions = relationship("KYCSession", back_populates="customer", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="customer", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_customer_email_status', 'email', 'customer_status'),
        Index('idx_customer_kyc_status', 'kyc_status'),
        Index('idx_customer_risk_level', 'risk_level'),
        Index('idx_customer_created_at', 'created_at'),
    )


# Document Models
class Document(Base):
    """Document information"""
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False)
    
    # Document Information
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    
    # Storage Information
    blob_name = Column(String(255), nullable=False)
    container_name = Column(String(100), nullable=False)
    blob_url = Column(String(500), nullable=False)
    
    # Processing Information
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Analysis Results
    extracted_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    analysis_results = Column(JSON, nullable=True)
    pii_detected = Column(Boolean, default=False, nullable=False)
    pii_redacted = Column(Boolean, default=False, nullable=False)
    authenticity_score = Column(Float, nullable=True)
    authenticity_status = Column(String(50), nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Metadata
    upload_source = Column(String(100), nullable=True)
    uploaded_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="documents")
    pii_detections = relationship("PIIDetection", back_populates="document", cascade="all, delete-orphan")
    authenticity_checks = relationship("AuthenticityCheck", back_populates="document", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_document_customer_id', 'customer_id'),
        Index('idx_document_type_status', 'document_type', 'status'),
        Index('idx_document_hash', 'file_hash'),
        Index('idx_document_uploaded_at', 'uploaded_at'),
    )


# KYC Session Models
class KYCSession(Base):
    """KYC processing session"""
    __tablename__ = "kyc_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False)
    
    # Session Information
    status = Column(SQLEnum(KYCStatus), default=KYCStatus.PENDING, nullable=False)
    session_type = Column(String(50), default="full_kyc", nullable=False)
    priority = Column(String(20), default="normal", nullable=False)
    
    # Processing Information
    current_step = Column(String(100), nullable=True)
    completion_percentage = Column(Float, default=0.0, nullable=False)
    required_documents = Column(JSON, nullable=True)  # List of required document types
    submitted_documents = Column(JSON, nullable=True)  # List of submitted document IDs
    
    # Results
    overall_risk_score = Column(Float, nullable=True)
    decision_reason = Column(Text, nullable=True)
    manual_review_required = Column(Boolean, default=False, nullable=False)
    manual_review_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # User Information
    assigned_to_user_id = Column(UUID(as_uuid=True), nullable=True)
    reviewed_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="kyc_sessions")
    workflow_steps = relationship("WorkflowStep", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_customer_id', 'customer_id'),
        Index('idx_session_status', 'status'),
        Index('idx_session_created_at', 'created_at'),
        Index('idx_session_assigned_user', 'assigned_to_user_id'),
    )


# User Management Models
class User(Base):
    """System users"""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User Information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False)
    department = Column(String(100), nullable=True)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Account Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # Relationships
    subordinates = relationship("User", backref="supervisor", remote_side=[user_id])
    audit_logs = relationship("AuditLog", back_populates="user")


# PII Detection Models
class PIIDetection(Base):
    """PII detection results"""
    __tablename__ = "pii_detections"

    detection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=False)
    
    # Detection Information
    pii_type = Column(String(100), nullable=False)
    detected_value = Column(String(500), nullable=True)  # May be redacted
    redacted_value = Column(String(500), nullable=True)
    confidence_score = Column(Float, nullable=False)
    position_start = Column(Integer, nullable=True)
    position_end = Column(Integer, nullable=True)
    
    # Detection Context
    context_before = Column(String(200), nullable=True)
    context_after = Column(String(200), nullable=True)
    detection_method = Column(String(100), nullable=False)
    
    # Status
    is_confirmed = Column(Boolean, default=False, nullable=False)
    is_redacted = Column(Boolean, default=False, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM, nullable=False)
    
    # Timestamps
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    redacted_at = Column(DateTime, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="pii_detections")


# Document Authenticity Models
class AuthenticityCheck(Base):
    """Document authenticity check results"""
    __tablename__ = "authenticity_checks"

    check_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=False)
    
    # Check Information
    check_type = Column(String(100), nullable=False)
    authenticity_score = Column(Float, nullable=False)
    is_authentic = Column(Boolean, nullable=False)
    confidence_level = Column(Float, nullable=False)
    
    # Check Results
    fraud_indicators = Column(JSON, nullable=True)
    check_details = Column(JSON, nullable=True)
    risk_factors = Column(JSON, nullable=True)
    
    # Analysis Method
    analysis_method = Column(String(100), nullable=False)
    azure_analysis_used = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="authenticity_checks")


# Risk Assessment Models
class RiskAssessment(Base):
    """Customer risk assessment"""
    __tablename__ = "risk_assessments"

    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False)
    
    # Assessment Information
    assessment_type = Column(String(100), nullable=False)
    overall_score = Column(Float, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    
    # Risk Factors
    risk_factors = Column(JSON, nullable=True)
    mitigating_factors = Column(JSON, nullable=True)
    
    # Assessment Details
    assessment_method = Column(String(100), nullable=False)
    assessor_user_id = Column(UUID(as_uuid=True), nullable=True)
    assessment_notes = Column(Text, nullable=True)
    
    # Status
    is_current = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    assessed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="risk_assessments")


# Workflow Models
class WorkflowStep(Base):
    """KYC workflow steps"""
    __tablename__ = "workflow_steps"

    step_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("kyc_sessions.session_id"), nullable=False)
    
    # Step Information
    step_name = Column(String(100), nullable=False)
    step_order = Column(Integer, nullable=False)
    step_type = Column(String(50), nullable=False)
    
    # Step Status
    status = Column(String(50), default="pending", nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    
    # Step Details
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Processing Information
    assigned_to_user_id = Column(UUID(as_uuid=True), nullable=True)
    processing_duration_seconds = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    session = relationship("KYCSession", back_populates="workflow_steps")


# Audit Models
class AuditLog(Base):
    """Comprehensive audit logging"""
    __tablename__ = "audit_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event Information
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    
    # User Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    username = Column(String(100), nullable=True)
    
    # Request Information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)
    
    # Event Details
    event_data = Column(JSON, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )
