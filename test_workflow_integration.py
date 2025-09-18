"""
Integration Tests for KYC Workflow System
Tests the complete automated KYC processing pipeline
"""
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from database.config import get_test_db
from database.models import Customer, Document, KYCSession, WorkflowStatus, RiskLevel
from database.repositories import get_customer_repo, get_document_repo, get_kyc_session_repo
from services.workflow_engine import workflow_engine
from services.risk_scorer import risk_scorer


class TestKYCWorkflowIntegration:
    """Integration tests for KYC workflow system"""
    
    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Set up test database"""
        self.db = get_test_db()
        yield
        self.db.close()
    
    @pytest.fixture
    def sample_customer(self):
        """Create a sample customer for testing"""
        customer_repo = get_customer_repo(self.db)
        
        customer_data = {
            "id": str(uuid.uuid4()),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "date_of_birth": datetime(1990, 1, 1).date(),
            "nationality": "US",
            "country": "United States",
            "city": "New York",
            "address_line_1": "123 Main St"
        }
        
        customer = customer_repo.create_customer(customer_data)
        self.db.commit()
        return customer
    
    @pytest.fixture
    def sample_documents(self, sample_customer):
        """Create sample documents for testing"""
        document_repo = get_document_repo(self.db)
        
        documents = []
        
        # Passport document
        passport_data = {
            "id": str(uuid.uuid4()),
            "customer_id": sample_customer.id,
            "document_type": "passport",
            "file_name": "passport.pdf",
            "file_size": 1024000,
            "mime_type": "application/pdf",
            "storage_path": "test/passport.pdf",
            "upload_timestamp": datetime.utcnow()
        }
        passport = document_repo.create_document(passport_data)
        documents.append(passport)
        
        # Driver's license document
        license_data = {
            "id": str(uuid.uuid4()),
            "customer_id": sample_customer.id,
            "document_type": "drivers_license",
            "file_name": "license.jpg",
            "file_size": 512000,
            "mime_type": "image/jpeg",
            "storage_path": "test/license.jpg",
            "upload_timestamp": datetime.utcnow()
        }
        license = document_repo.create_document(license_data)
        documents.append(license)
        
        self.db.commit()
        return documents
    
    @pytest.mark.asyncio
    async def test_complete_workflow_success(self, sample_customer, sample_documents):
        """Test complete successful KYC workflow"""
        # Mock Azure AI services
        with patch('services.document_analyzer.document_analyzer') as mock_analyzer, \
             patch('services.authenticity_checker.authenticity_checker') as mock_auth, \
             patch('services.pii_detector.pii_detector') as mock_pii:
            
            # Mock successful responses
            mock_analyzer.analyze_document.return_value = {
                "document_id": sample_documents[0].id,
                "extracted_text": "PASSPORT\nJohn Doe\nBorn: 1990-01-01",
                "quality_score": 0.95,
                "confidence": 0.98
            }
            
            mock_auth.verify_document_authenticity.return_value = {
                "authentic": True,
                "confidence_score": 0.92,
                "security_features": ["watermark", "microtext"],
                "fraud_indicators": []
            }
            
            mock_pii.detect_pii.return_value = {
                "entities": [
                    {"type": "person", "text": "John Doe", "confidence": 0.99},
                    {"type": "date", "text": "1990-01-01", "confidence": 0.95}
                ],
                "redacted_text": "[PERSON] passport, born [DATE]",
                "confidence_scores": {"person": 0.99, "date": 0.95}
            }
            
            # Start workflow
            session_id = str(uuid.uuid4())
            result = workflow_engine.process_customer_kyc(
                customer_id=sample_customer.id,
                session_id=session_id
            )
            
            # Verify workflow completed successfully
            assert result.status == WorkflowStatus.COMPLETED
            assert result.kyc_status.value in ['approved', 'pending_review']
            assert result.risk_assessment is not None
            assert len(result.workflow_steps) == 6
            
            # Verify all steps completed
            completed_steps = [step for step in result.workflow_steps if step.status == "completed"]
            assert len(completed_steps) == 6
    
    @pytest.mark.asyncio
    async def test_workflow_with_high_risk_customer(self, sample_customer, sample_documents):
        """Test workflow with high-risk customer requiring manual review"""
        # Modify customer to be high-risk
        sample_customer.country = "Afghanistan"  # High-risk country
        sample_customer.email = "test@tempmail.org"  # Suspicious email
        self.db.commit()
        
        # Mock Azure AI services
        with patch('services.document_analyzer.document_analyzer') as mock_analyzer, \
             patch('services.authenticity_checker.authenticity_checker') as mock_auth, \
             patch('services.pii_detector.pii_detector') as mock_pii:
            
            # Mock responses
            mock_analyzer.analyze_document.return_value = {
                "document_id": sample_documents[0].id,
                "extracted_text": "PASSPORT\nJohn Doe\nBorn: 1990-01-01",
                "quality_score": 0.6,  # Lower quality
                "confidence": 0.7
            }
            
            mock_auth.verify_document_authenticity.return_value = {
                "authentic": False,  # Failed authenticity
                "confidence_score": 0.3,
                "security_features": [],
                "fraud_indicators": ["suspicious_watermark"]
            }
            
            mock_pii.detect_pii.return_value = {
                "entities": [
                    {"type": "person", "text": "John Doe", "confidence": 0.6}  # Low confidence
                ],
                "redacted_text": "[PERSON] passport",
                "confidence_scores": {"person": 0.6}
            }
            
            # Start workflow
            session_id = str(uuid.uuid4())
            result = workflow_engine.process_customer_kyc(
                customer_id=sample_customer.id,
                session_id=session_id
            )
            
            # Verify workflow requires manual review
            assert result.status == WorkflowStatus.PENDING_REVIEW
            assert result.risk_assessment.risk_level == RiskLevel.HIGH
            assert len(result.risk_assessment.recommendations) > 0
    
    def test_risk_scoring_system(self, sample_customer, sample_documents):
        """Test risk scoring system independently"""
        # Test with normal customer
        assessment = risk_scorer.assess_customer_risk(sample_customer.id)
        
        assert assessment.customer_id == sample_customer.id
        assert 0.0 <= assessment.overall_risk_score <= 1.0
        assert assessment.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]
        assert 0.0 <= assessment.confidence_score <= 1.0
        assert len(assessment.risk_factors) >= 0
        assert len(assessment.recommendations) >= 1
        
        # Test with high-risk modifications
        sample_customer.country = "North Korea"
        sample_customer.email = "fake@guerrillamail.com"
        sample_customer.first_name = "Test"
        sample_customer.last_name = "User"
        self.db.commit()
        
        high_risk_assessment = risk_scorer.assess_customer_risk(sample_customer.id)
        
        # Should have higher risk score
        assert high_risk_assessment.overall_risk_score > assessment.overall_risk_score
        assert len(high_risk_assessment.risk_factors) > len(assessment.risk_factors)
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, sample_customer, sample_documents):
        """Test workflow error handling and retry mechanisms"""
        # Mock service failures
        with patch('services.document_analyzer.document_analyzer') as mock_analyzer:
            
            # Mock service failure
            mock_analyzer.analyze_document.side_effect = Exception("Service unavailable")
            
            # Start workflow
            session_id = str(uuid.uuid4())
            result = workflow_engine.process_customer_kyc(
                customer_id=sample_customer.id,
                session_id=session_id
            )
            
            # Verify workflow failed gracefully
            assert result.status in [WorkflowStatus.FAILED, WorkflowStatus.ERROR]
            assert result.error_message is not None
            
            # Verify some steps were attempted
            attempted_steps = [step for step in result.workflow_steps if step.status in ["completed", "failed", "error"]]
            assert len(attempted_steps) > 0
    
    def test_workflow_step_retry_logic(self, sample_customer, sample_documents):
        """Test workflow step retry logic"""
        from services.workflow_engine import WorkflowStep, WorkflowContext, WorkflowAction
        
        # Create workflow context
        context = WorkflowContext(
            customer_id=sample_customer.id,
            session_id=str(uuid.uuid4()),
            documents=[],
            processing_results={},
            risk_factors=[],
            current_step=0,
            retry_counts={}
        )
        
        # Test retry logic
        step = WorkflowStep(
            action=WorkflowAction.ANALYZE_DOCUMENTS,
            name="analyze_documents",
            description="Analyze uploaded documents",
            max_retries=3,
            timeout_seconds=300
        )
        
        # Simulate failure and retry
        context.retry_counts[step.action] = 2
        
        # Should allow retry (2 < 3)
        assert workflow_engine._should_retry_step(step, context, Exception("Test error"))
        
        # Simulate max retries reached
        context.retry_counts[step.action] = 3
        
        # Should not allow retry (3 >= 3)
        assert not workflow_engine._should_retry_step(step, context, Exception("Test error"))
    
    def test_workflow_session_persistence(self, sample_customer, sample_documents):
        """Test workflow session persistence in database"""
        kyc_repo = get_kyc_session_repo(self.db)
        
        # Create session
        session_data = {
            "id": str(uuid.uuid4()),
            "customer_id": sample_customer.id,
            "status": WorkflowStatus.PROCESSING,
            "priority": "normal",
            "created_at": datetime.utcnow()
        }
        
        session = kyc_repo.create_session(session_data)
        self.db.commit()
        
        # Verify session was saved
        retrieved_session = kyc_repo.get_session_by_id(session.id)
        assert retrieved_session is not None
        assert retrieved_session.customer_id == sample_customer.id
        assert retrieved_session.status == WorkflowStatus.PROCESSING
        
        # Test session updates
        retrieved_session.status = WorkflowStatus.COMPLETED
        kyc_repo.update_session(retrieved_session)
        self.db.commit()
        
        # Verify update
        updated_session = kyc_repo.get_session_by_id(session.id)
        assert updated_session.status == WorkflowStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_workflow_priority_handling(self, sample_customer, sample_documents):
        """Test workflow priority handling"""
        # Mock services
        with patch('services.document_analyzer.document_analyzer') as mock_analyzer, \
             patch('services.authenticity_checker.authenticity_checker') as mock_auth, \
             patch('services.pii_detector.pii_detector') as mock_pii:
            
            # Mock successful responses
            mock_analyzer.analyze_document.return_value = {"quality_score": 0.9}
            mock_auth.verify_document_authenticity.return_value = {"authentic": True}
            mock_pii.detect_pii.return_value = {"entities": []}
            
            # Test high priority workflow
            session_id = str(uuid.uuid4())
            result = workflow_engine.process_customer_kyc(
                customer_id=sample_customer.id,
                session_id=session_id,
                priority="urgent"
            )
            
            # Verify session has correct priority
            kyc_repo = get_kyc_session_repo(self.db)
            session = kyc_repo.get_session_by_id(session_id)
            assert session.priority == "urgent"
    
    def test_workflow_context_management(self, sample_customer, sample_documents):
        """Test workflow context data management"""
        from services.workflow_engine import WorkflowContext
        
        # Create context
        context = WorkflowContext(
            customer_id=sample_customer.id,
            session_id=str(uuid.uuid4()),
            documents=sample_documents,
            processing_results={},
            risk_factors=[],
            current_step=0,
            retry_counts={}
        )
        
        # Test context updates
        context.processing_results["document_analysis"] = {"status": "completed"}
        context.current_step = 1
        
        assert context.processing_results["document_analysis"]["status"] == "completed"
        assert context.current_step == 1
        
        # Test context serialization (for database storage)
        context_dict = {
            "customer_id": context.customer_id,
            "session_id": context.session_id,
            "current_step": context.current_step,
            "processing_results": context.processing_results,
            "retry_counts": context.retry_counts
        }
        
        assert context_dict["customer_id"] == sample_customer.id
        assert context_dict["current_step"] == 1
    
    def test_workflow_audit_logging(self, sample_customer, sample_documents):
        """Test workflow audit logging functionality"""
        from utils.audit_logger import get_audit_logs
        
        # Clear existing logs
        initial_log_count = len(get_audit_logs())
        
        # Start workflow (this should generate audit logs)
        with patch('services.document_analyzer.document_analyzer') as mock_analyzer:
            mock_analyzer.analyze_document.return_value = {"quality_score": 0.9}
            
            session_id = str(uuid.uuid4())
            workflow_engine.process_customer_kyc(
                customer_id=sample_customer.id,
                session_id=session_id
            )
        
        # Verify audit logs were created
        final_logs = get_audit_logs()
        assert len(final_logs) > initial_log_count
        
        # Check for specific workflow events
        workflow_events = [
            log for log in final_logs 
            if "workflow" in log.get("event_type", "").lower()
        ]
        assert len(workflow_events) > 0


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
