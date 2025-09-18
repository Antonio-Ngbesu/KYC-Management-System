"""
Document Retention Policy Service
Automated archival and deletion of documents based on configurable retention periods
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from azure.storage.blob import BlobServiceClient, BlobProperties
import json

from utils.audit_logger import log_security_event, AuditLevel
from services.blob_storage import blob_service_client, KYC_DOC_CONTAINER, KYC_PROCESSED_CONTAINER, KYC_ARCHIVES_CONTAINER

class RetentionAction(Enum):
    """Actions that can be taken on documents"""
    ARCHIVE = "archive"
    DELETE = "delete"
    EXTEND = "extend"
    REVIEW = "review"

class DocumentCategory(Enum):
    """Document categories with different retention requirements"""
    IDENTITY_DOCUMENT = "identity_document"
    FINANCIAL_DOCUMENT = "financial_document"
    UTILITY_DOCUMENT = "utility_document"
    BIOMETRIC_DATA = "biometric_data"
    AUDIT_DOCUMENT = "audit_document"

@dataclass
class RetentionPolicy:
    """Document retention policy definition"""
    category: DocumentCategory
    retention_period_days: int
    archive_period_days: int  # Time before archival
    action_after_retention: RetentionAction
    requires_approval: bool = False
    compliance_requirement: Optional[str] = None
    description: str = ""

@dataclass
class RetentionSchedule:
    """Scheduled retention action for a document"""
    document_id: str
    blob_name: str
    container_name: str
    category: DocumentCategory
    upload_date: datetime
    scheduled_action: RetentionAction
    scheduled_date: datetime
    policy_applied: str
    customer_id: Optional[str] = None
    processed: bool = False

class DocumentRetentionService:
    """Service for managing document retention and lifecycle"""
    
    def __init__(self):
        self.blob_client = blob_service_client
        
        # Default retention policies (in production, load from config/database)
        self.retention_policies = {
            DocumentCategory.IDENTITY_DOCUMENT: RetentionPolicy(
                category=DocumentCategory.IDENTITY_DOCUMENT,
                retention_period_days=2555,  # 7 years
                archive_period_days=1825,    # 5 years
                action_after_retention=RetentionAction.ARCHIVE,
                requires_approval=True,
                compliance_requirement="KYC Regulations",
                description="Identity documents must be retained for 7 years per KYC regulations"
            ),
            DocumentCategory.FINANCIAL_DOCUMENT: RetentionPolicy(
                category=DocumentCategory.FINANCIAL_DOCUMENT,
                retention_period_days=1825,  # 5 years
                archive_period_days=1095,    # 3 years
                action_after_retention=RetentionAction.ARCHIVE,
                requires_approval=True,
                compliance_requirement="Financial Regulations",
                description="Financial documents retained for 5 years per regulatory requirements"
            ),
            DocumentCategory.UTILITY_DOCUMENT: RetentionPolicy(
                category=DocumentCategory.UTILITY_DOCUMENT,
                retention_period_days=365,   # 1 year
                archive_period_days=180,     # 6 months
                action_after_retention=RetentionAction.DELETE,
                requires_approval=False,
                description="Utility documents for address verification"
            ),
            DocumentCategory.BIOMETRIC_DATA: RetentionPolicy(
                category=DocumentCategory.BIOMETRIC_DATA,
                retention_period_days=1095,  # 3 years
                archive_period_days=730,     # 2 years
                action_after_retention=RetentionAction.DELETE,
                requires_approval=True,
                compliance_requirement="Biometric Data Protection",
                description="Biometric data with strict privacy requirements"
            ),
            DocumentCategory.AUDIT_DOCUMENT: RetentionPolicy(
                category=DocumentCategory.AUDIT_DOCUMENT,
                retention_period_days=3650,  # 10 years
                archive_period_days=1825,    # 5 years
                action_after_retention=RetentionAction.ARCHIVE,
                requires_approval=True,
                compliance_requirement="Audit Trail Requirements",
                description="Audit documents for compliance and legal purposes"
            )
        }
        
        # Pending actions (in production, use database)
        self.pending_actions: List[RetentionSchedule] = []
        self.processed_actions: List[RetentionSchedule] = []
    
    def categorize_document(self, document_type: str, blob_metadata: Dict[str, str]) -> DocumentCategory:
        """Categorize document based on type and metadata"""
        
        document_type_lower = document_type.lower()
        
        if document_type_lower in ['passport', 'drivers_license', 'national_id']:
            return DocumentCategory.IDENTITY_DOCUMENT
        elif document_type_lower in ['bank_statement', 'tax_document']:
            return DocumentCategory.FINANCIAL_DOCUMENT
        elif document_type_lower in ['utility_bill']:
            return DocumentCategory.UTILITY_DOCUMENT
        elif document_type_lower in ['selfie', 'biometric']:
            return DocumentCategory.BIOMETRIC_DATA
        else:
            # Default to identity document for KYC purposes
            return DocumentCategory.IDENTITY_DOCUMENT
    
    def create_retention_schedule(self, blob_name: str, container_name: str, 
                                blob_metadata: Dict[str, str]) -> RetentionSchedule:
        """Create retention schedule for a document"""
        
        # Extract metadata
        document_type = blob_metadata.get('document_type', 'unknown')
        customer_id = blob_metadata.get('customer_id')
        upload_timestamp = blob_metadata.get('upload_timestamp')
        
        if upload_timestamp:
            upload_date = datetime.fromisoformat(upload_timestamp.replace('Z', '+00:00'))
        else:
            upload_date = datetime.now(timezone.utc)
        
        # Categorize document
        category = self.categorize_document(document_type, blob_metadata)
        policy = self.retention_policies[category]
        
        # Calculate scheduled dates
        archive_date = upload_date + timedelta(days=policy.archive_period_days)
        retention_date = upload_date + timedelta(days=policy.retention_period_days)
        
        # Determine next action
        now = datetime.now(timezone.utc)
        if now >= retention_date:
            scheduled_action = policy.action_after_retention
            scheduled_date = retention_date
        elif now >= archive_date and policy.action_after_retention == RetentionAction.ARCHIVE:
            scheduled_action = RetentionAction.ARCHIVE
            scheduled_date = archive_date
        else:
            # No immediate action needed
            scheduled_action = RetentionAction.REVIEW
            scheduled_date = archive_date
        
        # Extract document ID from blob name
        document_id = blob_name.split('/')[-1].split('.')[0]
        if '_' in document_id:
            document_id = document_id.split('_')[-1]
        
        return RetentionSchedule(
            document_id=document_id,
            blob_name=blob_name,
            container_name=container_name,
            category=category,
            upload_date=upload_date,
            scheduled_action=scheduled_action,
            scheduled_date=scheduled_date,
            policy_applied=f"{category.value}_policy",
            customer_id=customer_id
        )
    
    def scan_documents_for_retention(self) -> List[RetentionSchedule]:
        """Scan all documents and create retention schedules"""
        
        schedules = []
        containers = [KYC_DOC_CONTAINER, KYC_PROCESSED_CONTAINER]
        
        for container_name in containers:
            try:
                container_client = self.blob_client.get_container_client(container_name)
                
                for blob in container_client.list_blobs(include=['metadata']):
                    # Skip already processed documents
                    if any(s.blob_name == blob.name for s in self.processed_actions):
                        continue
                    
                    schedule = self.create_retention_schedule(
                        blob_name=blob.name,
                        container_name=container_name,
                        blob_metadata=blob.metadata or {}
                    )
                    
                    schedules.append(schedule)
                    
            except Exception as e:
                log_security_event(
                    event_type="retention_scan_error",
                    description=f"Error scanning container {container_name}: {str(e)}",
                    severity=AuditLevel.ERROR
                )
        
        return schedules
    
    def execute_retention_actions(self, approve_all: bool = False, 
                                 user_id: str = None) -> Dict[str, Any]:
        """Execute scheduled retention actions"""
        
        results = {
            "actions_executed": 0,
            "actions_skipped": 0,
            "actions_failed": 0,
            "details": []
        }
        
        # Get current schedules
        schedules = self.scan_documents_for_retention()
        current_time = datetime.now(timezone.utc)
        
        for schedule in schedules:
            if schedule.processed or schedule.scheduled_date > current_time:
                continue
            
            try:
                # Check if approval is required
                policy = self.retention_policies[schedule.category]
                if policy.requires_approval and not approve_all:
                    results["actions_skipped"] += 1
                    results["details"].append({
                        "document_id": schedule.document_id,
                        "action": "skipped",
                        "reason": "requires_approval",
                        "scheduled_action": schedule.scheduled_action.value
                    })
                    continue
                
                # Execute action
                success = self._execute_action(schedule, user_id)
                
                if success:
                    schedule.processed = True
                    self.processed_actions.append(schedule)
                    results["actions_executed"] += 1
                    results["details"].append({
                        "document_id": schedule.document_id,
                        "action": "executed",
                        "scheduled_action": schedule.scheduled_action.value,
                        "blob_name": schedule.blob_name
                    })
                else:
                    results["actions_failed"] += 1
                    results["details"].append({
                        "document_id": schedule.document_id,
                        "action": "failed",
                        "scheduled_action": schedule.scheduled_action.value
                    })
                    
            except Exception as e:
                results["actions_failed"] += 1
                results["details"].append({
                    "document_id": schedule.document_id,
                    "action": "failed",
                    "error": str(e)
                })
        
        # Log retention execution
        log_security_event(
            event_type="retention_executed",
            description=f"Retention actions executed: {results['actions_executed']} successful, {results['actions_failed']} failed",
            severity=AuditLevel.INFO,
            user_id=user_id,
            additional_details=results
        )
        
        return results
    
    def _execute_action(self, schedule: RetentionSchedule, user_id: str = None) -> bool:
        """Execute specific retention action"""
        
        try:
            if schedule.scheduled_action == RetentionAction.ARCHIVE:
                return self._archive_document(schedule, user_id)
            elif schedule.scheduled_action == RetentionAction.DELETE:
                return self._delete_document(schedule, user_id)
            elif schedule.scheduled_action == RetentionAction.EXTEND:
                return self._extend_retention(schedule, user_id)
            else:
                # No action needed for REVIEW
                return True
                
        except Exception as e:
            log_security_event(
                event_type="retention_action_failed",
                description=f"Failed to execute {schedule.scheduled_action.value} for document {schedule.document_id}: {str(e)}",
                severity=AuditLevel.ERROR,
                user_id=user_id
            )
            return False
    
    def _archive_document(self, schedule: RetentionSchedule, user_id: str = None) -> bool:
        """Archive document to long-term storage"""
        
        try:
            # Source blob
            source_container = self.blob_client.get_container_client(schedule.container_name)
            source_blob = source_container.get_blob_client(schedule.blob_name)
            
            # Destination blob in archives
            archive_container = self.blob_client.get_container_client(KYC_ARCHIVES_CONTAINER)
            archive_blob_name = f"archived_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{schedule.blob_name}"
            archive_blob = archive_container.get_blob_client(archive_blob_name)
            
            # Copy to archives
            archive_blob.start_copy_from_url(source_blob.url)
            
            # Update metadata to indicate archived status
            blob_metadata = source_blob.get_blob_properties().metadata or {}
            blob_metadata.update({
                "archived_date": datetime.now(timezone.utc).isoformat(),
                "archived_by": user_id or "system",
                "retention_status": "archived"
            })
            
            source_blob.set_blob_metadata(blob_metadata)
            
            log_security_event(
                event_type="document_archived",
                description=f"Document archived: {schedule.document_id}",
                severity=AuditLevel.INFO,
                user_id=user_id,
                additional_details={
                    "document_id": schedule.document_id,
                    "original_location": f"{schedule.container_name}/{schedule.blob_name}",
                    "archive_location": f"{KYC_ARCHIVES_CONTAINER}/{archive_blob_name}"
                }
            )
            
            return True
            
        except Exception as e:
            log_security_event(
                event_type="archive_failed",
                description=f"Failed to archive document {schedule.document_id}: {str(e)}",
                severity=AuditLevel.ERROR,
                user_id=user_id
            )
            return False
    
    def _delete_document(self, schedule: RetentionSchedule, user_id: str = None) -> bool:
        """Permanently delete document"""
        
        try:
            # Get blob client
            container_client = self.blob_client.get_container_client(schedule.container_name)
            blob_client = container_client.get_blob_client(schedule.blob_name)
            
            # Create deletion audit record before deleting
            blob_properties = blob_client.get_blob_properties()
            
            # Delete the blob
            blob_client.delete_blob()
            
            log_security_event(
                event_type="document_deleted",
                description=f"Document permanently deleted: {schedule.document_id}",
                severity=AuditLevel.WARNING,
                user_id=user_id,
                additional_details={
                    "document_id": schedule.document_id,
                    "blob_name": schedule.blob_name,
                    "container": schedule.container_name,
                    "category": schedule.category.value,
                    "retention_policy": schedule.policy_applied
                }
            )
            
            return True
            
        except Exception as e:
            log_security_event(
                event_type="deletion_failed",
                description=f"Failed to delete document {schedule.document_id}: {str(e)}",
                severity=AuditLevel.ERROR,
                user_id=user_id
            )
            return False
    
    def _extend_retention(self, schedule: RetentionSchedule, user_id: str = None) -> bool:
        """Extend retention period for document"""
        
        try:
            # Update scheduled date (extend by 1 year)
            schedule.scheduled_date = schedule.scheduled_date + timedelta(days=365)
            
            # Update blob metadata
            container_client = self.blob_client.get_container_client(schedule.container_name)
            blob_client = container_client.get_blob_client(schedule.blob_name)
            
            blob_metadata = blob_client.get_blob_properties().metadata or {}
            blob_metadata.update({
                "retention_extended": datetime.now(timezone.utc).isoformat(),
                "extended_by": user_id or "system",
                "new_retention_date": schedule.scheduled_date.isoformat()
            })
            
            blob_client.set_blob_metadata(blob_metadata)
            
            log_security_event(
                event_type="retention_extended",
                description=f"Retention period extended for document: {schedule.document_id}",
                severity=AuditLevel.INFO,
                user_id=user_id,
                additional_details={
                    "document_id": schedule.document_id,
                    "new_retention_date": schedule.scheduled_date.isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            log_security_event(
                event_type="extension_failed",
                description=f"Failed to extend retention for document {schedule.document_id}: {str(e)}",
                severity=AuditLevel.ERROR,
                user_id=user_id
            )
            return False
    
    def get_retention_report(self) -> Dict[str, Any]:
        """Generate retention status report"""
        
        schedules = self.scan_documents_for_retention()
        current_time = datetime.now(timezone.utc)
        
        report = {
            "scan_date": current_time.isoformat(),
            "total_documents": len(schedules),
            "by_category": {},
            "by_action": {},
            "immediate_actions_needed": 0,
            "upcoming_actions": [],
            "overdue_actions": []
        }
        
        for schedule in schedules:
            # By category
            category = schedule.category.value
            if category not in report["by_category"]:
                report["by_category"][category] = {"count": 0, "policy": self.retention_policies[schedule.category].description}
            report["by_category"][category]["count"] += 1
            
            # By action
            action = schedule.scheduled_action.value
            if action not in report["by_action"]:
                report["by_action"][action] = 0
            report["by_action"][action] += 1
            
            # Time-based analysis
            days_until_action = (schedule.scheduled_date - current_time).days
            
            if days_until_action < 0:
                report["overdue_actions"].append({
                    "document_id": schedule.document_id,
                    "action": action,
                    "overdue_days": abs(days_until_action),
                    "category": category
                })
            elif days_until_action <= 30:
                report["immediate_actions_needed"] += 1
                report["upcoming_actions"].append({
                    "document_id": schedule.document_id,
                    "action": action,
                    "days_until": days_until_action,
                    "category": category
                })
        
        return report
    
    def get_policy_info(self) -> Dict[str, Any]:
        """Get information about retention policies"""
        
        policy_info = {}
        for category, policy in self.retention_policies.items():
            policy_info[category.value] = {
                "retention_period_days": policy.retention_period_days,
                "archive_period_days": policy.archive_period_days,
                "action_after_retention": policy.action_after_retention.value,
                "requires_approval": policy.requires_approval,
                "compliance_requirement": policy.compliance_requirement,
                "description": policy.description
            }
        
        return policy_info

# Global retention service instance
retention_service = DocumentRetentionService()

# Convenience functions
def scan_and_execute_retention(approve_all: bool = False, user_id: str = None) -> Dict[str, Any]:
    """Scan documents and execute retention policies"""
    return retention_service.execute_retention_actions(approve_all, user_id)

def get_retention_status_report() -> Dict[str, Any]:
    """Get current retention status report"""
    return retention_service.get_retention_report()
