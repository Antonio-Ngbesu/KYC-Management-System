"""
KYC Workflow API Endpoints
Provides REST API for automated KYC workflow operations
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database.config import SessionLocal, get_db
from database.repositories import get_kyc_session_repo, get_customer_repo
from database.models import WorkflowStatus, RiskLevel, KYCStatus
from services.workflow_engine import workflow_engine
from services.risk_scorer import risk_scorer
from utils.audit_logger import log_security_event, AuditLevel
from api.auth import get_current_user, verify_admin_role


# Request/Response Models
class StartWorkflowRequest(BaseModel):
    customer_id: str = Field(..., description="Customer ID to process")
    priority: str = Field(default="normal", description="Processing priority (low, normal, high, urgent)")
    manual_review_required: bool = Field(default=False, description="Force manual review")
    additional_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context data")


class WorkflowStatusResponse(BaseModel):
    session_id: str
    customer_id: str
    status: str
    current_step: Optional[str]
    progress_percentage: float
    risk_score: Optional[float]
    risk_level: Optional[str]
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime]
    error_message: Optional[str]


class WorkflowStepResponse(BaseModel):
    step_id: str
    step_name: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int


class RiskAssessmentResponse(BaseModel):
    customer_id: str
    overall_risk_score: float
    risk_level: str
    confidence_score: float
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]
    assessment_timestamp: datetime


class WorkflowDecisionRequest(BaseModel):
    session_id: str
    decision: str = Field(..., description="approve, reject, or request_more_info")
    reviewer_notes: Optional[str] = Field(default=None, description="Reviewer comments")
    additional_requirements: Optional[List[str]] = Field(default=None, description="Additional requirements if requesting more info")


# Router setup
workflow_router = APIRouter(prefix="/api/v1/workflow", tags=["KYC Workflow"])
security = HTTPBearer()


@workflow_router.post("/start", response_model=Dict[str, str])
async def start_kyc_workflow(
    request: StartWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Start a new KYC workflow for a customer"""
    try:
        # Verify customer exists
        customer_repo = get_customer_repo(db)
        customer = customer_repo.get_customer_by_id(request.customer_id)
        
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer not found: {request.customer_id}")
        
        # Check if there's already an active workflow
        kyc_repo = get_kyc_session_repo(db)
        existing_session = kyc_repo.get_active_session_by_customer_id(request.customer_id)
        
        if existing_session:
            raise HTTPException(
                status_code=409, 
                detail=f"Active KYC session already exists: {existing_session.id}"
            )
        
        # Create new KYC session
        session_id = str(uuid.uuid4())
        
        # Start workflow in background
        background_tasks.add_task(
            _start_workflow_background,
            session_id,
            request.customer_id,
            request.priority,
            request.manual_review_required,
            request.additional_context or {},
            current_user.id
        )
        
        # Log workflow start
        log_security_event(
            event_type="kyc_workflow_started",
            description=f"KYC workflow started for customer: {request.customer_id}",
            severity=AuditLevel.INFO,
            additional_details={
                "session_id": session_id,
                "customer_id": request.customer_id,
                "priority": request.priority,
                "initiated_by": current_user.id
            }
        )
        
        return {
            "session_id": session_id,
            "message": "KYC workflow started successfully",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_security_event(
            event_type="kyc_workflow_start_error",
            description=f"Error starting KYC workflow: {str(e)}",
            severity=AuditLevel.ERROR,
            additional_details={"customer_id": request.customer_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Failed to start KYC workflow")


@workflow_router.get("/status/{session_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    session_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get the status of a KYC workflow session"""
    try:
        kyc_repo = get_kyc_session_repo(db)
        session = kyc_repo.get_session_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"KYC session not found: {session_id}")
        
        # Calculate progress percentage
        total_steps = 6  # Based on workflow engine steps
        completed_steps = len([step for step in session.workflow_steps if step.status == "completed"])
        progress_percentage = (completed_steps / total_steps) * 100
        
        # Get current step
        current_step = None
        for step in session.workflow_steps:
            if step.status == "in_progress":
                current_step = step.step_name
                break
        
        # Get risk assessment data
        risk_score = None
        risk_level = None
        if session.risk_assessment:
            risk_score = session.risk_assessment.risk_score
            risk_level = session.risk_assessment.risk_level.value
        
        return WorkflowStatusResponse(
            session_id=session.id,
            customer_id=session.customer_id,
            status=session.status.value,
            current_step=current_step,
            progress_percentage=progress_percentage,
            risk_score=risk_score,
            risk_level=risk_level,
            created_at=session.created_at,
            updated_at=session.updated_at,
            estimated_completion=session.estimated_completion,
            error_message=session.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get workflow status")


@workflow_router.get("/status/{session_id}/steps", response_model=List[WorkflowStepResponse])
async def get_workflow_steps(
    session_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get detailed step information for a KYC workflow session"""
    try:
        kyc_repo = get_kyc_session_repo(db)
        session = kyc_repo.get_session_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"KYC session not found: {session_id}")
        
        steps = []
        for step in session.workflow_steps:
            steps.append(WorkflowStepResponse(
                step_id=step.id,
                step_name=step.step_name,
                status=step.status,
                started_at=step.started_at,
                completed_at=step.completed_at,
                result=step.result,
                error_message=step.error_message,
                retry_count=step.retry_count
            ))
        
        return steps
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get workflow steps")


@workflow_router.get("/risk-assessment/{customer_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    customer_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get risk assessment for a customer"""
    try:
        # Verify customer exists
        customer_repo = get_customer_repo(db)
        customer = customer_repo.get_customer_by_id(customer_id)
        
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")
        
        # Perform risk assessment
        assessment = risk_scorer.assess_customer_risk(customer_id)
        
        # Convert risk factors to dict format
        risk_factors_dict = []
        for factor in assessment.risk_factors:
            risk_factors_dict.append({
                "category": factor.category.value,
                "factor_name": factor.factor_name,
                "weight": factor.weight,
                "score": factor.score,
                "description": factor.description,
                "evidence": factor.evidence
            })
        
        return RiskAssessmentResponse(
            customer_id=assessment.customer_id,
            overall_risk_score=assessment.overall_risk_score,
            risk_level=assessment.risk_level.value,
            confidence_score=assessment.confidence_score,
            risk_factors=risk_factors_dict,
            recommendations=assessment.recommendations,
            assessment_timestamp=assessment.assessment_timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get risk assessment")


@workflow_router.post("/decision")
async def submit_workflow_decision(
    request: WorkflowDecisionRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Submit a manual decision for a KYC workflow session"""
    try:
        kyc_repo = get_kyc_session_repo(db)
        session = kyc_repo.get_session_by_id(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"KYC session not found: {request.session_id}")
        
        if session.status != WorkflowStatus.PENDING_REVIEW:
            raise HTTPException(
                status_code=400, 
                detail=f"Session is not pending review. Current status: {session.status.value}"
            )
        
        # Validate decision
        valid_decisions = ["approve", "reject", "request_more_info"]
        if request.decision not in valid_decisions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid decision. Must be one of: {valid_decisions}"
            )
        
        # Update session with decision
        if request.decision == "approve":
            session.status = WorkflowStatus.APPROVED
            session.kyc_status = KYCStatus.APPROVED
        elif request.decision == "reject":
            session.status = WorkflowStatus.REJECTED
            session.kyc_status = KYCStatus.REJECTED
        else:  # request_more_info
            session.status = WorkflowStatus.ADDITIONAL_INFO_REQUIRED
            session.kyc_status = KYCStatus.PENDING
        
        # Add reviewer notes
        session.reviewer_notes = request.reviewer_notes
        session.reviewed_by = current_user.id
        session.reviewed_at = datetime.utcnow()
        
        # Update additional requirements if provided
        if request.additional_requirements:
            session.additional_requirements = request.additional_requirements
        
        db.commit()
        
        # Log decision
        log_security_event(
            event_type="kyc_workflow_decision",
            description=f"KYC workflow decision submitted: {request.decision}",
            severity=AuditLevel.INFO,
            additional_details={
                "session_id": request.session_id,
                "decision": request.decision,
                "reviewer": current_user.id,
                "customer_id": session.customer_id
            }
        )
        
        return {
            "message": f"Decision '{request.decision}' submitted successfully",
            "session_id": request.session_id,
            "status": session.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to submit workflow decision")


@workflow_router.get("/queue", response_model=List[WorkflowStatusResponse])
async def get_workflow_queue(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get the workflow queue for review"""
    try:
        # Verify user has access to workflow queue
        if not current_user.role in ['admin', 'analyst']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        kyc_repo = get_kyc_session_repo(db)
        
        # Build filters
        filters = {}
        if status:
            try:
                filters['status'] = WorkflowStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if priority:
            filters['priority'] = priority
        
        # Get sessions
        sessions = kyc_repo.get_sessions_by_filters(filters, limit=limit, offset=offset)
        
        # Convert to response format
        queue_items = []
        for session in sessions:
            # Calculate progress
            total_steps = 6
            completed_steps = len([step for step in session.workflow_steps if step.status == "completed"])
            progress_percentage = (completed_steps / total_steps) * 100
            
            # Get current step
            current_step = None
            for step in session.workflow_steps:
                if step.status == "in_progress":
                    current_step = step.step_name
                    break
            
            # Get risk data
            risk_score = None
            risk_level = None
            if session.risk_assessment:
                risk_score = session.risk_assessment.risk_score
                risk_level = session.risk_assessment.risk_level.value
            
            queue_items.append(WorkflowStatusResponse(
                session_id=session.id,
                customer_id=session.customer_id,
                status=session.status.value,
                current_step=current_step,
                progress_percentage=progress_percentage,
                risk_score=risk_score,
                risk_level=risk_level,
                created_at=session.created_at,
                updated_at=session.updated_at,
                estimated_completion=session.estimated_completion,
                error_message=session.error_message
            ))
        
        return queue_items
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get workflow queue")


@workflow_router.post("/retry/{session_id}")
async def retry_workflow(
    session_id: str,
    current_user = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Retry a failed KYC workflow"""
    try:
        # Verify admin role for retry operations
        verify_admin_role(current_user)
        
        kyc_repo = get_kyc_session_repo(db)
        session = kyc_repo.get_session_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"KYC session not found: {session_id}")
        
        if session.status not in [WorkflowStatus.FAILED, WorkflowStatus.ERROR]:
            raise HTTPException(
                status_code=400,
                detail=f"Session cannot be retried. Current status: {session.status.value}"
            )
        
        # Reset session status
        session.status = WorkflowStatus.PROCESSING
        session.error_message = None
        db.commit()
        
        # Retry workflow in background
        background_tasks.add_task(
            _retry_workflow_background,
            session_id,
            current_user.id
        )
        
        # Log retry
        log_security_event(
            event_type="kyc_workflow_retry",
            description=f"KYC workflow retry initiated: {session_id}",
            severity=AuditLevel.INFO,
            additional_details={
                "session_id": session_id,
                "retried_by": current_user.id
            }
        )
        
        return {
            "message": "Workflow retry initiated successfully",
            "session_id": session_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retry workflow")


# Background task functions
async def _start_workflow_background(
    session_id: str,
    customer_id: str,
    priority: str,
    manual_review_required: bool,
    additional_context: Dict[str, Any],
    initiated_by: str
):
    """Background task to start KYC workflow"""
    try:
        result = workflow_engine.process_customer_kyc(
            customer_id=customer_id,
            session_id=session_id,
            priority=priority,
            force_manual_review=manual_review_required,
            context=additional_context
        )
        
        log_security_event(
            event_type="kyc_workflow_completed",
            description=f"KYC workflow completed: {session_id}",
            severity=AuditLevel.INFO,
            additional_details={
                "session_id": session_id,
                "customer_id": customer_id,
                "final_status": result.status.value,
                "processing_time": (result.completed_at - result.created_at).total_seconds()
            }
        )
        
    except Exception as e:
        log_security_event(
            event_type="kyc_workflow_background_error",
            description=f"Error in background KYC workflow: {str(e)}",
            severity=AuditLevel.ERROR,
            additional_details={
                "session_id": session_id,
                "customer_id": customer_id,
                "error": str(e)
            }
        )


async def _retry_workflow_background(session_id: str, retried_by: str):
    """Background task to retry KYC workflow"""
    try:
        # Get session data
        db = SessionLocal()
        kyc_repo = get_kyc_session_repo(db)
        session = kyc_repo.get_session_by_id(session_id)
        
        if session:
            result = workflow_engine.retry_workflow(session_id)
            
            log_security_event(
                event_type="kyc_workflow_retry_completed",
                description=f"KYC workflow retry completed: {session_id}",
                severity=AuditLevel.INFO,
                additional_details={
                    "session_id": session_id,
                    "final_status": result.status.value,
                    "retried_by": retried_by
                }
            )
        
        db.close()
        
    except Exception as e:
        log_security_event(
            event_type="kyc_workflow_retry_error",
            description=f"Error in workflow retry: {str(e)}",
            severity=AuditLevel.ERROR,
            additional_details={
                "session_id": session_id,
                "retried_by": retried_by,
                "error": str(e)
            }
        )


# Export router
__all__ = ["workflow_router"]
