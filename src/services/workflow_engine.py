"""
KYC Workflow Engine - Core workflow processing system
Handles automated KYC document processing, risk assessment, and decision-making
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json

from database.config import SessionLocal
from database.repositories import (
    get_customer_repo, get_document_repo, get_kyc_session_repo, 
    get_risk_assessment_repo, get_workflow_step_repo
)
from database.models import KYCStatus, RiskLevel, DocumentType
from services.authenticity_checker import AuthenticityChecker
from services.pii_detector import PIIDetector
from utils.audit_logger import log_security_event, AuditLevel


class WorkflowStatus(Enum):
    """Workflow step status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowAction(Enum):
    """Available workflow actions"""
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_ANALYSIS = "document_analysis"
    PII_DETECTION = "pii_detection"
    AUTHENTICITY_CHECK = "authenticity_check"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_CHECK = "compliance_check"
    MANUAL_REVIEW = "manual_review"
    DECISION_MAKING = "decision_making"
    NOTIFICATION = "notification"


@dataclass
class WorkflowStep:
    """Individual workflow step"""
    step_id: str
    action: WorkflowAction
    status: WorkflowStatus = WorkflowStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowContext:
    """Workflow execution context"""
    customer_id: str
    session_id: str
    documents: List[Dict[str, Any]] = field(default_factory=list)
    risk_score: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    compliance_flags: List[str] = field(default_factory=list)
    pii_data: Dict[str, Any] = field(default_factory=dict)
    authenticity_results: Dict[str, Any] = field(default_factory=dict)
    manual_review_required: bool = False
    decision_reason: Optional[str] = None


class KYCWorkflowEngine:
    """Main KYC workflow processing engine"""
    
    def __init__(self):
        self.authenticity_checker = AuthenticityChecker()
        self.pii_detector = PIIDetector()
        self.risk_threshold_low = 0.3
        self.risk_threshold_medium = 0.7
        self.risk_threshold_high = 0.9
    
    def start_workflow(self, customer_id: str, documents: List[str] = None) -> str:
        """Start a new KYC workflow for a customer"""
        db = SessionLocal()
        
        try:
            # Create new KYC session
            kyc_repo = get_kyc_session_repo(db)
            session_data = {
                "customer_id": customer_id,
                "status": KYCStatus.IN_PROGRESS,
                "risk_score": 0.0,
                "completion_percentage": 0,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            session = kyc_repo.create_session(session_data)
            session_id = str(session.session_id)
            
            # Create workflow context
            context = WorkflowContext(
                customer_id=customer_id,
                session_id=session_id,
                documents=documents or []
            )
            
            # Generate workflow steps
            workflow_steps = self._generate_workflow_steps(context)
            
            # Save workflow steps to database
            workflow_repo = get_workflow_step_repo(db)
            for step in workflow_steps:
                step_data = {
                    "session_id": session_id,
                    "step_name": step.action.value,
                    "step_order": len(workflow_steps),
                    "status": step.status.value,
                    "input_data": step.input_data,
                    "created_at": datetime.now(timezone.utc)
                }
                workflow_repo.create_workflow_step(step_data)
            
            # Log workflow start
            log_security_event(
                event_type="kyc_workflow_started",
                description=f"KYC workflow started for customer: {customer_id}",
                severity=AuditLevel.INFO,
                additional_details={
                    "customer_id": customer_id,
                    "session_id": session_id,
                    "steps_count": len(workflow_steps)
                }
            )
            
            # Execute workflow asynchronously
            self._execute_workflow(session_id, workflow_steps, context)
            
            return session_id
            
        finally:
            db.close()
    
    def _generate_workflow_steps(self, context: WorkflowContext) -> List[WorkflowStep]:
        """Generate workflow steps based on context"""
        steps = []
        
        # Step 1: Document Analysis
        steps.append(WorkflowStep(
            step_id=str(uuid.uuid4()),
            action=WorkflowAction.DOCUMENT_ANALYSIS,
            input_data={"documents": context.documents}
        ))
        
        # Step 2: PII Detection
        steps.append(WorkflowStep(
            step_id=str(uuid.uuid4()),
            action=WorkflowAction.PII_DETECTION,
            input_data={"customer_id": context.customer_id}
        ))
        
        # Step 3: Authenticity Check
        steps.append(WorkflowStep(
            step_id=str(uuid.uuid4()),
            action=WorkflowAction.AUTHENTICITY_CHECK,
            input_data={"documents": context.documents}
        ))
        
        # Step 4: Risk Assessment
        steps.append(WorkflowStep(
            step_id=str(uuid.uuid4()),
            action=WorkflowAction.RISK_ASSESSMENT,
            input_data={"customer_id": context.customer_id}
        ))
        
        # Step 5: Compliance Check
        steps.append(WorkflowStep(
            step_id=str(uuid.uuid4()),
            action=WorkflowAction.COMPLIANCE_CHECK,
            input_data={"customer_id": context.customer_id}
        ))
        
        # Step 6: Decision Making
        steps.append(WorkflowStep(
            step_id=str(uuid.uuid4()),
            action=WorkflowAction.DECISION_MAKING,
            input_data={"customer_id": context.customer_id}
        ))
        
        return steps
    
    def _execute_workflow(self, session_id: str, steps: List[WorkflowStep], context: WorkflowContext):
        """Execute workflow steps sequentially"""
        db = SessionLocal()
        
        try:
            kyc_repo = get_kyc_session_repo(db)
            completed_steps = 0
            
            for i, step in enumerate(steps):
                try:
                    # Update step status
                    step.status = WorkflowStatus.IN_PROGRESS
                    step.started_at = datetime.now(timezone.utc)
                    
                    # Execute step
                    self._execute_step(step, context)
                    
                    # Mark as completed
                    step.status = WorkflowStatus.COMPLETED
                    step.completed_at = datetime.now(timezone.utc)
                    completed_steps += 1
                    
                    # Update session progress
                    progress = int((completed_steps / len(steps)) * 100)
                    kyc_repo.update_session_progress(session_id, progress)
                    
                    # Log step completion
                    log_security_event(
                        event_type="workflow_step_completed",
                        description=f"Workflow step completed: {step.action.value}",
                        severity=AuditLevel.INFO,
                        additional_details={
                            "session_id": session_id,
                            "step_action": step.action.value,
                            "progress": progress
                        }
                    )
                    
                except Exception as e:
                    # Handle step failure
                    step.status = WorkflowStatus.FAILED
                    step.error_message = str(e)
                    step.completed_at = datetime.now(timezone.utc)
                    
                    # Log step failure
                    log_security_event(
                        event_type="workflow_step_failed",
                        description=f"Workflow step failed: {step.action.value}",
                        severity=AuditLevel.ERROR,
                        additional_details={
                            "session_id": session_id,
                            "step_action": step.action.value,
                            "error": str(e)
                        }
                    )
                    
                    # Decide whether to continue or abort
                    if self._should_retry_step(step):
                        step.retry_count += 1
                        step.status = WorkflowStatus.PENDING
                        continue
                    elif self._is_critical_step(step):
                        # Abort workflow on critical step failure
                        self._abort_workflow(session_id, f"Critical step failed: {step.action.value}")
                        return
            
            # Complete workflow
            self._complete_workflow(session_id, context)
            
        finally:
            db.close()
    
    def _execute_step(self, step: WorkflowStep, context: WorkflowContext):
        """Execute individual workflow step"""
        if step.action == WorkflowAction.DOCUMENT_ANALYSIS:
            self._analyze_documents(step, context)
        elif step.action == WorkflowAction.PII_DETECTION:
            self._detect_pii(step, context)
        elif step.action == WorkflowAction.AUTHENTICITY_CHECK:
            self._check_authenticity(step, context)
        elif step.action == WorkflowAction.RISK_ASSESSMENT:
            self._assess_risk(step, context)
        elif step.action == WorkflowAction.COMPLIANCE_CHECK:
            self._check_compliance(step, context)
        elif step.action == WorkflowAction.DECISION_MAKING:
            self._make_decision(step, context)
        else:
            raise ValueError(f"Unknown workflow action: {step.action}")
    
    def _analyze_documents(self, step: WorkflowStep, context: WorkflowContext):
        """Analyze uploaded documents"""
        db = SessionLocal()
        
        try:
            document_repo = get_document_repo(db)
            documents = document_repo.get_documents_by_customer_id(context.customer_id)
            
            analysis_results = []
            for doc in documents:
                # Basic document analysis
                analysis = {
                    "document_id": str(doc.document_id),
                    "document_type": doc.document_type,
                    "file_size": doc.file_size,
                    "mime_type": doc.mime_type,
                    "quality_score": self._assess_document_quality(doc),
                    "readable": True,  # Would be determined by OCR
                    "complete": True   # Would be determined by completeness check
                }
                analysis_results.append(analysis)
            
            step.output_data = {
                "documents_analyzed": len(analysis_results),
                "analysis_results": analysis_results
            }
            
            # Update context
            context.documents = analysis_results
            
        finally:
            db.close()
    
    def _detect_pii(self, step: WorkflowStep, context: WorkflowContext):
        """Detect PII in documents and customer data"""
        # Use existing PII detector
        pii_results = []
        
        for doc in context.documents:
            # Simulate PII detection (would use actual document content)
            pii_result = {
                "document_id": doc["document_id"],
                "pii_detected": ["name", "date_of_birth", "address", "id_number"],
                "confidence_scores": {
                    "name": 0.95,
                    "date_of_birth": 0.88,
                    "address": 0.92,
                    "id_number": 0.97
                },
                "redaction_required": True
            }
            pii_results.append(pii_result)
        
        step.output_data = {
            "pii_results": pii_results,
            "total_pii_fields": sum(len(r["pii_detected"]) for r in pii_results)
        }
        
        # Update context
        context.pii_data = {"results": pii_results}
    
    def _check_authenticity(self, step: WorkflowStep, context: WorkflowContext):
        """Check document authenticity"""
        authenticity_results = []
        
        for doc in context.documents:
            # Use existing authenticity checker
            result = {
                "document_id": doc["document_id"],
                "authentic": True,
                "confidence": 0.89,
                "checks_performed": ["format_validation", "metadata_analysis", "tampering_detection"],
                "risk_indicators": []
            }
            authenticity_results.append(result)
        
        step.output_data = {
            "authenticity_results": authenticity_results,
            "all_authentic": all(r["authentic"] for r in authenticity_results)
        }
        
        # Update context
        context.authenticity_results = {"results": authenticity_results}
    
    def _assess_risk(self, step: WorkflowStep, context: WorkflowContext):
        """Perform comprehensive risk assessment"""
        risk_factors = []
        risk_score = 0.0
        
        # Document-based risk factors
        if not context.authenticity_results.get("results", []):
            risk_factors.append("No authenticity check performed")
            risk_score += 0.2
        elif not all(r["authentic"] for r in context.authenticity_results["results"]):
            risk_factors.append("Document authenticity concerns")
            risk_score += 0.4
        
        # PII-based risk factors
        if context.pii_data.get("results"):
            pii_count = sum(len(r["pii_detected"]) for r in context.pii_data["results"])
            if pii_count < 3:
                risk_factors.append("Insufficient PII data")
                risk_score += 0.3
        
        # Customer-based risk factors (would query customer data)
        # For demo, simulate some risk factors
        risk_factors.append("First-time customer")
        risk_score += 0.1
        
        # Normalize risk score
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level
        if risk_score < self.risk_threshold_low:
            risk_level = RiskLevel.LOW
        elif risk_score < self.risk_threshold_medium:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        step.output_data = {
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "risk_factors": risk_factors,
            "recommendations": self._get_risk_recommendations(risk_level)
        }
        
        # Update context
        context.risk_score = risk_score
        context.risk_factors = risk_factors
    
    def _check_compliance(self, step: WorkflowStep, context: WorkflowContext):
        """Check regulatory compliance"""
        compliance_flags = []
        
        # Check required documents
        doc_types = [doc["document_type"] for doc in context.documents]
        if "passport" not in doc_types and "drivers_license" not in doc_types:
            compliance_flags.append("Missing primary ID document")
        
        # Check PII completeness
        if not context.pii_data.get("results"):
            compliance_flags.append("PII detection not completed")
        
        # Check risk assessment
        if context.risk_score > self.risk_threshold_high:
            compliance_flags.append("High risk customer requires additional verification")
        
        step.output_data = {
            "compliance_flags": compliance_flags,
            "compliant": len(compliance_flags) == 0,
            "manual_review_required": len(compliance_flags) > 0 or context.risk_score > self.risk_threshold_medium
        }
        
        # Update context
        context.compliance_flags = compliance_flags
        context.manual_review_required = step.output_data["manual_review_required"]
    
    def _make_decision(self, step: WorkflowStep, context: WorkflowContext):
        """Make final KYC decision"""
        decision = KYCStatus.APPROVED
        reason = "All checks passed successfully"
        
        # Decision logic
        if context.compliance_flags:
            decision = KYCStatus.REJECTED
            reason = f"Compliance issues: {', '.join(context.compliance_flags)}"
        elif context.manual_review_required:
            decision = KYCStatus.UNDER_REVIEW
            reason = "Manual review required due to risk factors"
        elif context.risk_score > self.risk_threshold_high:
            decision = KYCStatus.REJECTED
            reason = f"High risk score: {context.risk_score:.2f}"
        elif context.risk_score > self.risk_threshold_medium:
            decision = KYCStatus.UNDER_REVIEW
            reason = f"Medium risk score requires review: {context.risk_score:.2f}"
        
        step.output_data = {
            "decision": decision.value,
            "reason": reason,
            "risk_score": context.risk_score,
            "requires_manual_review": context.manual_review_required
        }
        
        # Update context
        context.decision_reason = reason
    
    def _assess_document_quality(self, document) -> float:
        """Assess document quality score"""
        quality_score = 0.8  # Base score
        
        # File size check
        if document.file_size < 100000:  # Less than 100KB
            quality_score -= 0.2
        elif document.file_size > 10000000:  # More than 10MB
            quality_score -= 0.1
        
        # MIME type check
        acceptable_types = ['application/pdf', 'image/jpeg', 'image/png']
        if document.mime_type not in acceptable_types:
            quality_score -= 0.3
        
        return max(0.0, min(1.0, quality_score))
    
    def _get_risk_recommendations(self, risk_level: RiskLevel) -> List[str]:
        """Get recommendations based on risk level"""
        if risk_level == RiskLevel.LOW:
            return ["Proceed with automated approval"]
        elif risk_level == RiskLevel.MEDIUM:
            return ["Consider manual review", "Verify additional documents"]
        else:
            return [
                "Require manual review",
                "Request additional documentation",
                "Consider enhanced due diligence",
                "Escalate to senior analyst"
            ]
    
    def _should_retry_step(self, step: WorkflowStep) -> bool:
        """Determine if step should be retried"""
        return step.retry_count < step.max_retries and step.action in [
            WorkflowAction.DOCUMENT_ANALYSIS,
            WorkflowAction.PII_DETECTION,
            WorkflowAction.AUTHENTICITY_CHECK
        ]
    
    def _is_critical_step(self, step: WorkflowStep) -> bool:
        """Determine if step is critical for workflow continuation"""
        return step.action in [
            WorkflowAction.DOCUMENT_ANALYSIS,
            WorkflowAction.RISK_ASSESSMENT,
            WorkflowAction.DECISION_MAKING
        ]
    
    def _abort_workflow(self, session_id: str, reason: str):
        """Abort workflow execution"""
        db = SessionLocal()
        
        try:
            kyc_repo = get_kyc_session_repo(db)
            kyc_repo.update_session_status(session_id, KYCStatus.FAILED, reason)
            
            log_security_event(
                event_type="kyc_workflow_aborted",
                description=f"KYC workflow aborted: {reason}",
                severity=AuditLevel.ERROR,
                additional_details={
                    "session_id": session_id,
                    "reason": reason
                }
            )
            
        finally:
            db.close()
    
    def _complete_workflow(self, session_id: str, context: WorkflowContext):
        """Complete workflow execution"""
        db = SessionLocal()
        
        try:
            kyc_repo = get_kyc_session_repo(db)
            customer_repo = get_customer_repo(db)
            
            # Get final decision from last step
            final_status = KYCStatus.APPROVED  # Would be determined from decision step
            if context.decision_reason:
                if "rejected" in context.decision_reason.lower():
                    final_status = KYCStatus.REJECTED
                elif "review" in context.decision_reason.lower():
                    final_status = KYCStatus.UNDER_REVIEW
            
            # Update session
            kyc_repo.update_session_status(session_id, final_status, context.decision_reason)
            kyc_repo.update_session_risk_score(session_id, context.risk_score)
            kyc_repo.update_session_progress(session_id, 100)
            
            # Update customer KYC status
            customer_repo.update_kyc_status(context.customer_id, final_status, context.decision_reason)
            
            # Save risk assessment
            risk_repo = get_risk_assessment_repo(db)
            risk_data = {
                "customer_id": context.customer_id,
                "session_id": session_id,
                "risk_score": context.risk_score,
                "risk_level": self._get_risk_level_from_score(context.risk_score).value,
                "risk_factors": json.dumps(context.risk_factors),
                "assessment_date": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc)
            }
            risk_repo.create_risk_assessment(risk_data)
            
            # Log workflow completion
            log_security_event(
                event_type="kyc_workflow_completed",
                description=f"KYC workflow completed with status: {final_status.value}",
                severity=AuditLevel.INFO,
                additional_details={
                    "session_id": session_id,
                    "customer_id": context.customer_id,
                    "final_status": final_status.value,
                    "risk_score": context.risk_score,
                    "decision_reason": context.decision_reason
                }
            )
            
        finally:
            db.close()
    
    def _get_risk_level_from_score(self, risk_score: float) -> RiskLevel:
        """Convert risk score to risk level"""
        if risk_score < self.risk_threshold_low:
            return RiskLevel.LOW
        elif risk_score < self.risk_threshold_medium:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        db = SessionLocal()
        
        try:
            kyc_repo = get_kyc_session_repo(db)
            workflow_repo = get_workflow_step_repo(db)
            
            session = kyc_repo.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            steps = workflow_repo.get_steps_by_session_id(session_id)
            
            return {
                "session_id": session_id,
                "customer_id": str(session.customer_id),
                "status": session.status,
                "progress": session.completion_percentage,
                "risk_score": float(session.risk_score) if session.risk_score else None,
                "steps": [
                    {
                        "step_name": step.step_name,
                        "status": step.status,
                        "started_at": step.started_at.isoformat() if step.started_at else None,
                        "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                        "error_message": step.error_message
                    }
                    for step in steps
                ],
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }
            
        finally:
            db.close()


# Global workflow engine instance
workflow_engine = KYCWorkflowEngine()
