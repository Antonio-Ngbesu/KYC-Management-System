"""
Repository pattern for database operations
Provides clean interfaces for database CRUD operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timezone
import uuid

from database.models import Customer, Document, KYCSession, User, AuditLog, PIIDetection, AuthenticityCheck, RiskAssessment
from database.config import get_db
from models.kyc_models import DocumentType, DocumentStatus, KYCStatus
from auth.models import UserRole


class BaseRepository:
    """Base repository with common operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def commit(self):
        """Commit transaction"""
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
    
    def rollback(self):
        """Rollback transaction"""
        self.db.rollback()


class CustomerRepository(BaseRepository):
    """Repository for Customer operations"""
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """Create a new customer"""
        customer = Customer(**customer_data)
        self.db.add(customer)
        self.commit()
        self.db.refresh(customer)
        return customer
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        return self.db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    def get_customer_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        return self.db.query(Customer).filter(Customer.email == email).first()
    
    def get_customer_by_external_id(self, external_id: str) -> Optional[Customer]:
        """Get customer by external ID"""
        return self.db.query(Customer).filter(Customer.external_customer_id == external_id).first()
    
    def update_customer(self, customer_id: str, update_data: Dict[str, Any]) -> Optional[Customer]:
        """Update customer information"""
        customer = self.get_customer(customer_id)
        if not customer:
            return None
        
        for key, value in update_data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        
        customer.updated_at = datetime.now(timezone.utc)
        self.commit()
        self.db.refresh(customer)
        return customer
    
    def update_kyc_status(self, customer_id: str, status: KYCStatus, notes: str = None) -> Optional[Customer]:
        """Update customer KYC status"""
        customer = self.get_customer(customer_id)
        if not customer:
            return None
        
        customer.kyc_status = status
        customer.updated_at = datetime.now(timezone.utc)
        
        if status in [KYCStatus.APPROVED, KYCStatus.REJECTED]:
            customer.kyc_completed_at = datetime.now(timezone.utc)
        
        if notes:
            customer.notes = notes
        
        self.commit()
        self.db.refresh(customer)
        return customer
    
    def get_customers_by_status(self, status: KYCStatus, limit: int = 100, offset: int = 0) -> List[Customer]:
        """Get customers by KYC status"""
        return (self.db.query(Customer)
                .filter(Customer.kyc_status == status)
                .order_by(desc(Customer.created_at))
                .offset(offset)
                .limit(limit)
                .all())
    
    def search_customers(self, search_term: str = "", filters: Dict[str, Any] = None) -> List[Customer]:
        """Search customers with advanced filters"""
        query = self.db.query(Customer)
        
        # Apply search term if provided
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(or_(
                Customer.first_name.ilike(search_pattern),
                Customer.last_name.ilike(search_pattern),
                Customer.email.ilike(search_pattern),
                Customer.phone.ilike(search_pattern)
            ))
        
        # Apply filters if provided
        if filters:
            if 'kyc_status' in filters:
                if isinstance(filters['kyc_status'], list):
                    query = query.filter(Customer.kyc_status.in_(filters['kyc_status']))
                else:
                    query = query.filter(Customer.kyc_status == filters['kyc_status'])
            
            if 'risk_level' in filters:
                if isinstance(filters['risk_level'], list):
                    query = query.filter(Customer.risk_level.in_(filters['risk_level']))
                else:
                    query = query.filter(Customer.risk_level == filters['risk_level'])
            
            if 'country' in filters:
                query = query.filter(Customer.country == filters['country'])
            
            if 'is_active' in filters:
                query = query.filter(Customer.is_active == filters['is_active'])
            
            if 'created_after' in filters:
                query = query.filter(Customer.created_at >= filters['created_after'])
            
            if 'created_before' in filters:
                query = query.filter(Customer.created_at <= filters['created_before'])
        
        # Apply ordering
        query = query.order_by(desc(Customer.created_at))
        
        # Apply pagination
        if filters:
            if 'offset' in filters:
                query = query.offset(filters['offset'])
            if 'limit' in filters:
                query = query.limit(filters['limit'])
        
        return query.all()
    
    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID (alias for get_customer)"""
        return self.get_customer(customer_id)
    
    def get_customer_statistics(self) -> Dict[str, Any]:
        """Get customer statistics for dashboard"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Basic counts
        total_customers = self.db.query(Customer).count()
        active_customers = self.db.query(Customer).filter(Customer.is_active == True).count()
        inactive_customers = total_customers - active_customers
        
        # KYC status breakdown
        kyc_status_data = (self.db.query(Customer.kyc_status, func.count(Customer.customer_id))
                          .group_by(Customer.kyc_status)
                          .all())
        kyc_status_breakdown = {status: count for status, count in kyc_status_data}
        
        # Risk level breakdown
        risk_level_data = (self.db.query(Customer.risk_level, func.count(Customer.customer_id))
                          .group_by(Customer.risk_level)
                          .all())
        risk_level_breakdown = {level: count for level, count in risk_level_data}
        
        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_registrations = (self.db.query(Customer)
                               .filter(Customer.created_at >= thirty_days_ago)
                               .count())
        
        # Specific KYC counts
        pending_kyc_count = kyc_status_breakdown.get(KYCStatus.PENDING, 0)
        approved_kyc_count = kyc_status_breakdown.get(KYCStatus.APPROVED, 0)
        rejected_kyc_count = kyc_status_breakdown.get(KYCStatus.REJECTED, 0)
        
        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "inactive_customers": inactive_customers,
            "kyc_status_breakdown": kyc_status_breakdown,
            "risk_level_breakdown": risk_level_breakdown,
            "recent_registrations": recent_registrations,
            "pending_kyc_count": pending_kyc_count,
            "approved_kyc_count": approved_kyc_count,
            "rejected_kyc_count": rejected_kyc_count
        }


class DocumentRepository(BaseRepository):
    """Repository for Document operations"""
    
    def create_document(self, document_data: Dict[str, Any]) -> Document:
        """Create a new document"""
        document = Document(**document_data)
        self.db.add(document)
        self.commit()
        self.db.refresh(document)
        return document
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        return self.db.query(Document).filter(Document.document_id == document_id).first()
    
    def get_customer_documents(self, customer_id: str, document_type: DocumentType = None) -> List[Document]:
        """Get all documents for a customer"""
        query = self.db.query(Document).filter(Document.customer_id == customer_id)
        
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        return query.order_by(desc(Document.uploaded_at)).all()
    
    def get_documents_by_customer_id(self, customer_id: str) -> List[Document]:
        """Get all documents for a customer (alias for get_customer_documents)"""
        return self.get_customer_documents(customer_id)
    
    def update_document_status(self, document_id: str, status: DocumentStatus, error: str = None) -> Optional[Document]:
        """Update document processing status"""
        document = self.get_document(document_id)
        if not document:
            return None
        
        document.status = status
        document.updated_at = datetime.now(timezone.utc)
        
        if status == DocumentStatus.PROCESSING:
            document.processing_started_at = datetime.now(timezone.utc)
        elif status in [DocumentStatus.PROCESSED, DocumentStatus.FAILED]:
            document.processing_completed_at = datetime.now(timezone.utc)
        
        if error:
            document.processing_error = error
        
        self.commit()
        self.db.refresh(document)
        return document
    
    def update_document_analysis(self, document_id: str, analysis_data: Dict[str, Any]) -> Optional[Document]:
        """Update document analysis results"""
        document = self.get_document(document_id)
        if not document:
            return None
        
        for key, value in analysis_data.items():
            if hasattr(document, key):
                setattr(document, key, value)
        
        document.updated_at = datetime.now(timezone.utc)
        self.commit()
        self.db.refresh(document)
        return document
    
    def get_documents_by_hash(self, file_hash: str) -> List[Document]:
        """Find documents with the same hash (duplicates)"""
        return self.db.query(Document).filter(Document.file_hash == file_hash).all()
    
    def get_pending_documents(self, limit: int = 100) -> List[Document]:
        """Get documents pending processing"""
        return (self.db.query(Document)
                .filter(Document.status.in_([DocumentStatus.UPLOADED, DocumentStatus.PROCESSING]))
                .order_by(asc(Document.uploaded_at))
                .limit(limit)
                .all())


class KYCSessionRepository(BaseRepository):
    """Repository for KYC Session operations"""
    
    def create_session(self, session_data: Dict[str, Any]) -> KYCSession:
        """Create a new KYC session"""
        session = KYCSession(**session_data)
        self.db.add(session)
        self.commit()
        self.db.refresh(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[KYCSession]:
        """Get KYC session by ID"""
        return self.db.query(KYCSession).filter(KYCSession.session_id == session_id).first()
    
    def get_customer_sessions(self, customer_id: str) -> List[KYCSession]:
        """Get all KYC sessions for a customer"""
        return (self.db.query(KYCSession)
                .filter(KYCSession.customer_id == customer_id)
                .order_by(desc(KYCSession.created_at))
                .all())
    
    def get_sessions_by_customer_id(self, customer_id: str) -> List[KYCSession]:
        """Get all KYC sessions for a customer (alias for get_customer_sessions)"""
        return self.get_customer_sessions(customer_id)
    
    def get_active_session(self, customer_id: str) -> Optional[KYCSession]:
        """Get active KYC session for customer"""
        return (self.db.query(KYCSession)
                .filter(and_(
                    KYCSession.customer_id == customer_id,
                    KYCSession.status.in_([KYCStatus.PENDING, KYCStatus.IN_PROGRESS])
                ))
                .order_by(desc(KYCSession.created_at))
                .first())
    
    def update_session_status(self, session_id: str, status: KYCStatus, notes: str = None) -> Optional[KYCSession]:
        """Update KYC session status"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        old_status = session.status
        session.status = status
        session.updated_at = datetime.now(timezone.utc)
        
        if status == KYCStatus.IN_PROGRESS and old_status == KYCStatus.PENDING:
            session.started_at = datetime.now(timezone.utc)
        elif status in [KYCStatus.APPROVED, KYCStatus.REJECTED]:
            session.completed_at = datetime.now(timezone.utc)
        
        if notes:
            session.decision_reason = notes
        
        self.commit()
        self.db.refresh(session)
        return session
    
    def update_session_progress(self, session_id: str, percentage: float, current_step: str = None) -> Optional[KYCSession]:
        """Update session progress"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        session.completion_percentage = percentage
        if current_step:
            session.current_step = current_step
        session.updated_at = datetime.now(timezone.utc)
        
        self.commit()
        self.db.refresh(session)
        return session


class UserRepository(BaseRepository):
    """Repository for User operations"""
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        user = User(**user_data)
        self.db.add(user)
        self.commit()
        self.db.refresh(user)
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[User]:
        """Update user information"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now(timezone.utc)
        self.commit()
        self.db.refresh(user)
        return user
    
    def update_login_info(self, user_id: str, success: bool = True) -> Optional[User]:
        """Update user login information"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        if success:
            user.last_login_at = datetime.now(timezone.utc)
            user.failed_login_attempts = 0
            user.locked_until = None
        else:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                # Lock account for 30 minutes
                user.locked_until = datetime.now(timezone.utc).replace(minute=datetime.now().minute + 30)
        
        self.commit()
        self.db.refresh(user)
        return user
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        return self.db.query(User).filter(User.role == role, User.is_active == True).all()


class AuditRepository(BaseRepository):
    """Repository for Audit Log operations"""
    
    def create_audit_log(self, log_data: Dict[str, Any]) -> AuditLog:
        """Create a new audit log entry"""
        audit_log = AuditLog(**log_data)
        self.db.add(audit_log)
        self.commit()
        self.db.refresh(audit_log)
        return audit_log
    
    def get_audit_logs(self, 
                      user_id: str = None,
                      action: str = None,
                      resource_type: str = None,
                      limit: int = 1000,
                      offset: int = 0) -> List[AuditLog]:
        """Get audit logs with filters"""
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        return (query.order_by(desc(AuditLog.timestamp))
                .offset(offset)
                .limit(limit)
                .all())
    
    def get_user_activity(self, user_id: str, days: int = 30) -> List[AuditLog]:
        """Get user activity for the last N days"""
        from datetime import timedelta
        
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        return (self.db.query(AuditLog)
                .filter(and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= since_date
                ))
                .order_by(desc(AuditLog.timestamp))
                .all())


# Convenience functions for getting repository instances
def get_customer_repo(db: Session = None) -> CustomerRepository:
    """Get customer repository instance"""
    if not db:
        db = next(get_db())
    return CustomerRepository(db)

def get_document_repo(db: Session = None) -> DocumentRepository:
    """Get document repository instance"""
    if not db:
        db = next(get_db())
    return DocumentRepository(db)

def get_session_repo(db: Session = None) -> KYCSessionRepository:
    """Get KYC session repository instance"""
    if not db:
        db = next(get_db())
    return KYCSessionRepository(db)

def get_user_repo(db: Session = None) -> UserRepository:
    """Get user repository instance"""
    if not db:
        db = next(get_db())
    return UserRepository(db)

def get_audit_repo(db: Session = None) -> AuditRepository:
    """Get audit repository instance"""
    if not db:
        db = next(get_db())
    return AuditRepository(db)
