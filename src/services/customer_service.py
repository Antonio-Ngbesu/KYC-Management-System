"""
Customer management service for KYC Document Analyzer
Handles customer profile management, KYC status tracking, and document association
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database.config import SessionLocal
from database.repositories import get_customer_repo, get_document_repo, get_kyc_session_repo
from database.models import Customer as DBCustomer, KYCStatus, RiskLevel
from auth.models import User, Permission
from utils.audit_logger import log_security_event, AuditLevel


class CustomerService:
    """Service for managing customer data and KYC processes"""
    
    def create_customer(self, customer_data: Dict[str, Any], created_by_user_id: str) -> Dict[str, Any]:
        """Create a new customer profile"""
        db = SessionLocal()
        
        try:
            customer_repo = get_customer_repo(db)
            
            # Generate customer ID if not provided
            if 'customer_id' not in customer_data:
                customer_data['customer_id'] = str(uuid.uuid4())
            
            # Set default values
            customer_data.update({
                'kyc_status': customer_data.get('kyc_status', KYCStatus.PENDING),
                'risk_level': customer_data.get('risk_level', RiskLevel.MEDIUM),
                'is_active': customer_data.get('is_active', True),
                'created_by': created_by_user_id,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            })
            
            # Create customer in database
            db_customer = customer_repo.create_customer(customer_data)
            
            # Log customer creation
            log_security_event(
                event_type="customer_created",
                description=f"New customer created: {customer_data.get('first_name', '')} {customer_data.get('last_name', '')}",
                severity=AuditLevel.INFO,
                user_id=created_by_user_id,
                additional_details={
                    "customer_id": str(db_customer.customer_id),
                    "email": customer_data.get('email', ''),
                    "phone": customer_data.get('phone', '')
                }
            )
            
            return self._format_customer_response(db_customer)
            
        finally:
            db.close()
    
    def get_customer(self, customer_id: str, requesting_user_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID with permission check"""
        db = SessionLocal()
        
        try:
            customer_repo = get_customer_repo(db)
            db_customer = customer_repo.get_customer_by_id(customer_id)
            
            if not db_customer:
                return None
            
            # Log customer access
            log_security_event(
                event_type="customer_accessed",
                description=f"Customer profile accessed: {db_customer.first_name} {db_customer.last_name}",
                severity=AuditLevel.INFO,
                user_id=requesting_user_id,
                additional_details={"customer_id": customer_id}
            )
            
            return self._format_customer_response(db_customer)
            
        finally:
            db.close()
    
    def update_customer(self, customer_id: str, updates: Dict[str, Any], updated_by_user_id: str) -> Optional[Dict[str, Any]]:
        """Update customer information"""
        db = SessionLocal()
        
        try:
            customer_repo = get_customer_repo(db)
            
            # Add update metadata
            updates.update({
                'updated_by': updated_by_user_id,
                'updated_at': datetime.now(timezone.utc)
            })
            
            db_customer = customer_repo.update_customer(customer_id, updates)
            
            if not db_customer:
                return None
            
            # Log customer update
            log_security_event(
                event_type="customer_updated",
                description=f"Customer profile updated: {db_customer.first_name} {db_customer.last_name}",
                severity=AuditLevel.INFO,
                user_id=updated_by_user_id,
                additional_details={
                    "customer_id": customer_id,
                    "updated_fields": list(updates.keys())
                }
            )
            
            return self._format_customer_response(db_customer)
            
        finally:
            db.close()
    
    def search_customers(self, query: str, filters: Dict[str, Any] = None, requesting_user_id: str = None) -> List[Dict[str, Any]]:
        """Search customers with filters"""
        db = SessionLocal()
        
        try:
            customer_repo = get_customer_repo(db)
            db_customers = customer_repo.search_customers(query, filters)
            
            # Log search activity
            if requesting_user_id:
                log_security_event(
                    event_type="customer_search",
                    description=f"Customer search performed: '{query}'",
                    severity=AuditLevel.INFO,
                    user_id=requesting_user_id,
                    additional_details={
                        "query": query,
                        "filters": filters,
                        "results_count": len(db_customers)
                    }
                )
            
            return [self._format_customer_response(customer) for customer in db_customers]
            
        finally:
            db.close()
    
    def get_customer_documents(self, customer_id: str, requesting_user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a customer"""
        db = SessionLocal()
        
        try:
            document_repo = get_document_repo(db)
            db_documents = document_repo.get_documents_by_customer_id(customer_id)
            
            # Log document access
            log_security_event(
                event_type="customer_documents_accessed",
                description=f"Customer documents accessed for customer: {customer_id}",
                severity=AuditLevel.INFO,
                user_id=requesting_user_id,
                additional_details={
                    "customer_id": customer_id,
                    "documents_count": len(db_documents)
                }
            )
            
            return [self._format_document_response(doc) for doc in db_documents]
            
        finally:
            db.close()
    
    def get_customer_kyc_sessions(self, customer_id: str, requesting_user_id: str) -> List[Dict[str, Any]]:
        """Get all KYC sessions for a customer"""
        db = SessionLocal()
        
        try:
            kyc_repo = get_kyc_session_repo(db)
            db_sessions = kyc_repo.get_sessions_by_customer_id(customer_id)
            
            return [self._format_kyc_session_response(session) for session in db_sessions]
            
        finally:
            db.close()
    
    def update_kyc_status(self, customer_id: str, new_status: KYCStatus, updated_by_user_id: str, notes: str = None) -> Optional[Dict[str, Any]]:
        """Update customer KYC status"""
        db = SessionLocal()
        
        try:
            customer_repo = get_customer_repo(db)
            
            # Get current customer
            db_customer = customer_repo.get_customer_by_id(customer_id)
            if not db_customer:
                return None
            
            old_status = db_customer.kyc_status
            
            # Update status
            updates = {
                'kyc_status': new_status,
                'kyc_status_updated_at': datetime.now(timezone.utc),
                'updated_by': updated_by_user_id,
                'updated_at': datetime.now(timezone.utc)
            }
            
            if notes:
                updates['notes'] = notes
            
            db_customer = customer_repo.update_customer(customer_id, updates)
            
            # Log status change
            log_security_event(
                event_type="kyc_status_changed",
                description=f"KYC status changed from {old_status} to {new_status} for customer: {db_customer.first_name} {db_customer.last_name}",
                severity=AuditLevel.WARNING,
                user_id=updated_by_user_id,
                additional_details={
                    "customer_id": customer_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "notes": notes
                }
            )
            
            return self._format_customer_response(db_customer)
            
        finally:
            db.close()
    
    def get_customer_statistics(self, requesting_user_id: str) -> Dict[str, Any]:
        """Get customer statistics for dashboard"""
        db = SessionLocal()
        
        try:
            customer_repo = get_customer_repo(db)
            stats = customer_repo.get_customer_statistics()
            
            # Log statistics access
            log_security_event(
                event_type="customer_statistics_accessed",
                description="Customer statistics accessed",
                severity=AuditLevel.INFO,
                user_id=requesting_user_id
            )
            
            return stats
            
        finally:
            db.close()
    
    def _format_customer_response(self, db_customer: DBCustomer) -> Dict[str, Any]:
        """Format customer database model to API response"""
        return {
            "customer_id": str(db_customer.customer_id),
            "first_name": db_customer.first_name,
            "last_name": db_customer.last_name,
            "email": db_customer.email,
            "phone": db_customer.phone,
            "date_of_birth": db_customer.date_of_birth.isoformat() if db_customer.date_of_birth else None,
            "address_line_1": db_customer.address_line_1,
            "address_line_2": db_customer.address_line_2,
            "city": db_customer.city,
            "state": db_customer.state,
            "postal_code": db_customer.postal_code,
            "country": db_customer.country,
            "nationality": db_customer.nationality,
            "kyc_status": db_customer.kyc_status,
            "risk_level": db_customer.risk_level,
            "kyc_status_updated_at": db_customer.kyc_status_updated_at.isoformat() if db_customer.kyc_status_updated_at else None,
            "is_active": db_customer.is_active,
            "created_at": db_customer.created_at.isoformat(),
            "updated_at": db_customer.updated_at.isoformat(),
            "created_by": db_customer.created_by,
            "updated_by": db_customer.updated_by,
            "notes": db_customer.notes
        }
    
    def _format_document_response(self, db_document) -> Dict[str, Any]:
        """Format document database model to API response"""
        return {
            "document_id": str(db_document.document_id),
            "customer_id": str(db_document.customer_id),
            "document_type": db_document.document_type,
            "file_name": db_document.file_name,
            "file_size": db_document.file_size,
            "mime_type": db_document.mime_type,
            "storage_path": db_document.storage_path,
            "upload_status": db_document.upload_status,
            "processing_status": db_document.processing_status,
            "created_at": db_document.created_at.isoformat(),
            "updated_at": db_document.updated_at.isoformat()
        }
    
    def _format_kyc_session_response(self, db_session) -> Dict[str, Any]:
        """Format KYC session database model to API response"""
        return {
            "session_id": str(db_session.session_id),
            "customer_id": str(db_session.customer_id),
            "status": db_session.status,
            "risk_score": float(db_session.risk_score) if db_session.risk_score else None,
            "completion_percentage": db_session.completion_percentage,
            "created_at": db_session.created_at.isoformat(),
            "updated_at": db_session.updated_at.isoformat(),
            "completed_at": db_session.completed_at.isoformat() if db_session.completed_at else None
        }


# Global service instance
customer_service = CustomerService()
