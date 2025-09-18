"""
Document upload service for KYC processing
Enhanced with security and compliance features
"""
import os
import uuid
import time
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from models.kyc_models import DocumentType, DocumentMetadata, DocumentStatus
from utils.audit_logger import log_document_upload, log_document_processing, log_pii_access, log_security_event, AuditLevel
from services.pii_redaction import detect_and_redact_image, detect_and_redact_text
from services.authenticity_checker import verify_document_authenticity

load_dotenv()

class DocumentUploadService:
    """Service for handling document uploads to Azure Blob Storage"""
    
    def __init__(self):
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Container names
        self.kyc_doc_container = "kyc-doc"
        self.kyc_processed_container = "kyc-processed"
        self.kyc_archives_container = "kyc-archives"
        
        # Allowed file types
        self.allowed_mime_types = {
            DocumentType.PASSPORT: ["image/jpeg", "image/png", "image/jpg", "application/pdf"],
            DocumentType.DRIVERS_LICENSE: ["image/jpeg", "image/png", "image/jpg", "application/pdf"],
            DocumentType.NATIONAL_ID: ["image/jpeg", "image/png", "image/jpg", "application/pdf"],
            DocumentType.UTILITY_BILL: ["image/jpeg", "image/png", "image/jpg", "application/pdf"],
            DocumentType.BANK_STATEMENT: ["application/pdf", "image/jpeg", "image/png", "image/jpg"],
            DocumentType.SELFIE: ["image/jpeg", "image/png", "image/jpg"]
        }
        
        # Max file size (10MB)
        self.max_file_size = 10 * 1024 * 1024

    def validate_file(self, file: UploadFile, document_type: DocumentType) -> None:
        """Validate uploaded file"""
        # Check file size
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {self.max_file_size / (1024*1024)}MB"
            )
        
        # Check MIME type
        if file.content_type not in self.allowed_mime_types[document_type]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types for {document_type}: {self.allowed_mime_types[document_type]}"
            )
    
    def generate_blob_name(self, customer_id: str, document_type: DocumentType, filename: str) -> str:
        """Generate unique blob name"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = filename.split('.')[-1] if '.' in filename else 'unknown'
        document_id = str(uuid.uuid4())
        
        return f"{customer_id}/{document_type.value}/{timestamp}_{document_id}.{file_extension}"
    
    async def upload_document(
        self, 
        file: UploadFile, 
        customer_id: str, 
        document_type: DocumentType,
        user_id: str = None,
        ip_address: str = None
    ) -> Tuple[DocumentMetadata, Dict[str, Any]]:
        """Upload document to Azure Blob Storage with security checks"""
        
        # Validate file
        self.validate_file(file, document_type)
        
        # Generate unique blob name
        blob_name = self.generate_blob_name(customer_id, document_type, file.filename or "unknown")
        document_id = blob_name.split('/')[-1].split('.')[0].split('_')[-1]
        
        start_time = time.time()
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Log document upload
            log_document_upload(
                document_id=document_id,
                filename=file.filename or "unknown",
                file_size=len(file_content),
                document_type=document_type.value,
                user_id=user_id,
                ip_address=ip_address
            )
            
            # Security and compliance checks
            security_results = await self._perform_security_checks(
                file_content, document_id, document_type, user_id
            )
            
            # Check if document fails critical security checks
            if security_results.get("risk_level") == "CRITICAL":
                log_security_event(
                    event_type="high_risk_upload",
                    description=f"Critical security issues detected in document {document_id}",
                    severity=AuditLevel.CRITICAL,
                    user_id=user_id,
                    ip_address=ip_address,
                    additional_details=security_results
                )
                raise HTTPException(
                    status_code=400,
                    detail="Document upload blocked due to security concerns"
                )
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.kyc_doc_container,
                blob=blob_name
            )
            
            # Upload to blob storage (use redacted version if available)
            upload_content = security_results.get("redacted_content", file_content)
            
            blob_client.upload_blob(
                upload_content,
                blob_type="BlockBlob",
                overwrite=True,
                metadata={
                    "customer_id": customer_id,
                    "document_type": document_type.value,
                    "original_filename": file.filename or "unknown",
                    "upload_timestamp": datetime.utcnow().isoformat(),
                    "security_checked": "true",
                    "pii_redacted": str(security_results.get("pii_redacted", False)),
                    "authenticity_score": str(security_results.get("authenticity_score", 0))
                }
            )
            
            # Create metadata
            metadata = DocumentMetadata(
                document_id=document_id,
                customer_id=customer_id,
                document_type=document_type,
                original_filename=file.filename or "unknown",
                file_size=len(file_content),
                mime_type=file.content_type or "unknown",
                upload_timestamp=datetime.utcnow(),
                status=DocumentStatus.UPLOADED,
                blob_url=blob_client.url,
                container_name=self.kyc_doc_container
            )
            
            # Log successful processing
            processing_time = time.time() - start_time
            log_document_processing(
                document_id=document_id,
                processing_result="success",
                processing_time=processing_time,
                services_used=["upload", "security_check", "pii_redaction", "authenticity_check"],
                user_id=user_id
            )
            
            return metadata, security_results
            
        except HTTPException:
            raise
        except Exception as e:
            # Log error
            log_security_event(
                event_type="upload_error",
                description=f"Upload failed for document {document_id}: {str(e)}",
                severity=AuditLevel.ERROR,
                user_id=user_id,
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload document: {str(e)}"
            )
    
    async def _perform_security_checks(
        self, 
        file_content: bytes, 
        document_id: str, 
        document_type: DocumentType,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Perform comprehensive security and compliance checks"""
        
        security_results = {
            "document_id": document_id,
            "pii_redacted": False,
            "authenticity_score": 1.0,
            "risk_level": "LOW",
            "security_checks": {}
        }
        
        try:
            # 1. Document Authenticity Check
            if self._is_image_file(file_content):
                authenticity_result = verify_document_authenticity(
                    file_content, document_type.value
                )
                security_results["security_checks"]["authenticity"] = authenticity_result
                security_results["authenticity_score"] = authenticity_result["confidence_score"]
                
                # Update risk level based on authenticity
                if authenticity_result["document_authenticity"] == "likely_fraud":
                    security_results["risk_level"] = "HIGH"
                elif authenticity_result["document_authenticity"] == "confirmed_fraud":
                    security_results["risk_level"] = "CRITICAL"
            
            # 2. PII Detection and Redaction
            if self._is_image_file(file_content):
                redacted_content, pii_matches, pii_report = detect_and_redact_image(
                    file_content, document_id
                )
                
                if pii_matches:
                    security_results["pii_redacted"] = True
                    security_results["redacted_content"] = redacted_content
                    security_results["security_checks"]["pii"] = pii_report
                    
                    # Log PII access
                    pii_fields = list(set(match.pii_type for match in pii_matches))
                    log_pii_access(
                        document_id=document_id,
                        pii_fields_accessed=pii_fields,
                        access_reason="document_upload_processing",
                        user_id=user_id
                    )
                    
                    # Update risk level based on PII
                    if pii_report["risk_level"] in ["HIGH", "CRITICAL"]:
                        security_results["risk_level"] = max(
                            security_results["risk_level"], 
                            pii_report["risk_level"],
                            key=lambda x: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(x)
                        )
            
            # 3. File Security Checks
            file_security = self._check_file_security(file_content)
            security_results["security_checks"]["file_security"] = file_security
            
            if file_security["risk_level"] == "HIGH":
                security_results["risk_level"] = max(
                    security_results["risk_level"], 
                    "HIGH",
                    key=lambda x: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(x)
                )
            
            return security_results
            
        except Exception as e:
            log_security_event(
                event_type="security_check_error",
                description=f"Security check failed for document {document_id}: {str(e)}",
                severity=AuditLevel.WARNING,
                user_id=user_id
            )
            # Return basic results if security checks fail
            return security_results
    
    def _is_image_file(self, file_content: bytes) -> bool:
        """Check if file is an image based on content"""
        # Check for common image file signatures
        image_signatures = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF
            b'GIF89a',  # GIF
        ]
        
        for signature in image_signatures:
            if file_content.startswith(signature):
                return True
        return False
    
    def _check_file_security(self, file_content: bytes) -> Dict[str, Any]:
        """Basic file security checks"""
        results = {
            "file_size": len(file_content),
            "suspicious_content": False,
            "risk_level": "LOW",
            "checks": []
        }
        
        # Check for suspiciously small files
        if len(file_content) < 1024:  # Less than 1KB
            results["checks"].append("File unusually small")
            results["risk_level"] = "MEDIUM"
        
        # Check for suspicious file headers (basic malware detection)
        suspicious_headers = [
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
            b'PK\x03\x04',  # ZIP file (could contain malware)
        ]
        
        for header in suspicious_headers:
            if file_content.startswith(header):
                results["suspicious_content"] = True
                results["risk_level"] = "HIGH"
                results["checks"].append(f"Suspicious file header detected")
                break
        
        return results
    
    def get_document_url(self, blob_name: str, container_name: str = None) -> str:
        """Get URL for document"""
        if container_name is None:
            container_name = self.kyc_doc_container
            
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        return blob_client.url
    
    def move_document_to_processed(self, blob_name: str) -> str:
        """Move document from kyc-doc to kyc-processed"""
        try:
            # Source blob
            source_blob = self.blob_service_client.get_blob_client(
                container=self.kyc_doc_container,
                blob=blob_name
            )
            
            # Destination blob
            dest_blob = self.blob_service_client.get_blob_client(
                container=self.kyc_processed_container,
                blob=blob_name
            )
            
            # Copy to processed container
            dest_blob.start_copy_from_url(source_blob.url)
            
            # Delete from original container
            source_blob.delete_blob()
            
            return dest_blob.url
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to move document: {str(e)}"
            )

# Global instance
upload_service = DocumentUploadService()
