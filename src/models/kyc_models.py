"""
Data models for KYC Document Analyzer
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class DocumentType(str, Enum):
    """Types of documents that can be uploaded"""
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    SELFIE = "selfie"

class DocumentStatus(str, Enum):
    """Status of document processing"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class KYCStatus(str, Enum):
    """Overall KYC status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"

class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    document_type: DocumentType
    customer_id: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class DocumentMetadata(BaseModel):
    """Metadata for uploaded documents"""
    document_id: str
    customer_id: str
    document_type: DocumentType
    original_filename: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    status: DocumentStatus = DocumentStatus.UPLOADED
    blob_url: str
    container_name: str

class DocumentAnalysisResult(BaseModel):
    """Result from document analysis"""
    document_id: str
    extracted_text: Optional[str] = None
    key_value_pairs: Optional[dict] = None
    tables: Optional[List[dict]] = None
    confidence_score: Optional[float] = None
    analysis_timestamp: datetime
    
class FaceVerificationResult(BaseModel):
    """Result from face verification"""
    document_id: str
    selfie_document_id: str
    is_match: bool
    confidence_score: float
    verification_timestamp: datetime

class EntityExtractionResult(BaseModel):
    """Result from entity extraction"""
    document_id: str
    entities: List[dict]
    extraction_timestamp: datetime

class KYCSession(BaseModel):
    """Complete KYC session"""
    session_id: str
    customer_id: str
    status: KYCStatus = KYCStatus.PENDING
    created_timestamp: datetime
    updated_timestamp: datetime
    documents: List[DocumentMetadata] = []
    analysis_results: List[DocumentAnalysisResult] = []
    verification_results: List[FaceVerificationResult] = []
    entity_results: List[EntityExtractionResult] = []

class UploadResponse(BaseModel):
    """Response after successful upload"""
    success: bool
    message: str
    document_id: str
    document_metadata: DocumentMetadata
