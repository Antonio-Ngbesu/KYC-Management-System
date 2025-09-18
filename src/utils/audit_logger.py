"""
Audit logging system for KYC Document Analyzer
Tracks all document processing activities for compliance and security
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum

class AuditAction(Enum):
    """Types of auditable actions"""
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_PROCESS = "document_process"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DELETE = "document_delete"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_CHANGE = "permission_change"
    DATA_EXPORT = "data_export"
    PII_ACCESS = "pii_access"
    SYSTEM_ERROR = "system_error"

class AuditLevel(Enum):
    """Audit severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditLogger:
    """Centralized audit logging for compliance tracking"""
    
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Configure audit logger
        self.logger = logging.getLogger("kyc_audit")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        
        # File handler for audit logs
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # JSON formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.propagate = False  # Prevent duplicate logs in main logger
    
    def log_audit_event(
        self,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[str] = None,
        document_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log an audit event with comprehensive details"""
        
        audit_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action.value,
            "level": level.value,
            "user_id": user_id or "anonymous",
            "document_id": document_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {},
            "session_id": self._get_session_id()  # You can implement session tracking
        }
        
        # Log based on severity level
        log_message = json.dumps(audit_record, ensure_ascii=False)
        
        if level == AuditLevel.CRITICAL:
            self.logger.critical(log_message)
        elif level == AuditLevel.ERROR:
            self.logger.error(log_message)
        elif level == AuditLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def log_document_upload(
        self,
        document_id: str,
        filename: str,
        file_size: int,
        document_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log document upload event"""
        details = {
            "filename": filename,
            "file_size_bytes": file_size,
            "document_type": document_type,
            "upload_method": "api"
        }
        
        self.log_audit_event(
            action=AuditAction.DOCUMENT_UPLOAD,
            level=AuditLevel.INFO,
            user_id=user_id,
            document_id=document_id,
            details=details,
            ip_address=ip_address
        )
    
    def log_document_processing(
        self,
        document_id: str,
        processing_result: str,
        processing_time: float,
        services_used: list,
        user_id: Optional[str] = None,
        extracted_data: Optional[Dict] = None
    ):
        """Log document processing event"""
        details = {
            "processing_result": processing_result,
            "processing_time_seconds": processing_time,
            "services_used": services_used,
            "data_extracted": bool(extracted_data),
            "extraction_fields": list(extracted_data.keys()) if extracted_data else []
        }
        
        level = AuditLevel.INFO if processing_result == "success" else AuditLevel.WARNING
        
        self.log_audit_event(
            action=AuditAction.DOCUMENT_PROCESS,
            level=level,
            user_id=user_id,
            document_id=document_id,
            details=details
        )
    
    def log_pii_access(
        self,
        document_id: str,
        pii_fields: list,
        access_reason: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log access to personally identifiable information"""
        details = {
            "pii_fields": pii_fields,
            "access_reason": access_reason,
            "redaction_applied": False  # Will be updated by PII redaction service
        }
        
        self.log_audit_event(
            action=AuditAction.PII_ACCESS,
            level=AuditLevel.WARNING,  # PII access should be closely monitored
            user_id=user_id,
            document_id=document_id,
            details=details,
            ip_address=ip_address
        )
    
    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: AuditLevel = AuditLevel.WARNING,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_details: Optional[Dict] = None
    ):
        """Log security-related events"""
        details = {
            "event_type": event_type,
            "description": description,
            **(additional_details or {})
        }
        
        self.log_audit_event(
            action=AuditAction.SYSTEM_ERROR if severity == AuditLevel.ERROR else AuditAction.USER_LOGIN,
            level=severity,
            user_id=user_id,
            details=details,
            ip_address=ip_address
        )
    
    def log_data_export(
        self,
        export_type: str,
        records_count: int,
        file_format: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log data export activities"""
        details = {
            "export_type": export_type,
            "records_count": records_count,
            "file_format": file_format,
            "export_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.log_audit_event(
            action=AuditAction.DATA_EXPORT,
            level=AuditLevel.WARNING,  # Data exports should be monitored
            user_id=user_id,
            details=details,
            ip_address=ip_address
        )
    
    def _get_session_id(self) -> Optional[str]:
        """Get current session ID - implement based on your session management"""
        # This would be implemented based on your authentication system
        return None
    
    def get_audit_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get audit summary for the last N days"""
        # This would parse the audit log and return summary statistics
        # Implementation depends on your specific needs
        return {
            "period_days": days,
            "total_events": 0,
            "events_by_action": {},
            "events_by_user": {},
            "security_events": 0
        }

# Global audit logger instance
audit_logger = AuditLogger("logs/audit.log")

# Convenience functions for common operations
def log_document_upload(document_id: str, filename: str, file_size: int, 
                       document_type: str, user_id: str = None, ip_address: str = None):
    """Convenience function for logging document uploads"""
    audit_logger.log_document_upload(
        document_id, filename, file_size, document_type, user_id, ip_address
    )

def log_document_processing(document_id: str, processing_result: str, 
                          processing_time: float, services_used: list, 
                          user_id: str = None, extracted_data: Dict = None):
    """Convenience function for logging document processing"""
    audit_logger.log_document_processing(
        document_id, processing_result, processing_time, services_used, user_id, extracted_data
    )

def log_pii_access(document_id: str, pii_fields: list, access_reason: str, 
                  user_id: str = None, ip_address: str = None):
    """Convenience function for logging PII access"""
    audit_logger.log_pii_access(document_id, pii_fields, access_reason, user_id, ip_address)

def log_security_event(event_type: str, description: str, severity: AuditLevel = AuditLevel.WARNING,
                      user_id: str = None, ip_address: str = None, additional_details: Dict = None):
    """Convenience function for logging security events"""
    audit_logger.log_security_event(event_type, description, severity, user_id, ip_address, additional_details)
