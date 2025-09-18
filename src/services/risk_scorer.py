"""
Advanced Risk Scoring System for KYC Document Analyzer
Implements sophisticated risk assessment algorithms and scoring models
"""
import json
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from database.config import SessionLocal
from database.repositories import get_customer_repo, get_document_repo, get_risk_assessment_repo
from database.models import RiskLevel, KYCStatus
from utils.audit_logger import log_security_event, AuditLevel


class RiskCategory(Enum):
    """Risk assessment categories"""
    IDENTITY_VERIFICATION = "identity_verification"
    DOCUMENT_QUALITY = "document_quality"
    BEHAVIORAL_PATTERNS = "behavioral_patterns"
    GEOGRAPHIC_RISK = "geographic_risk"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    FRAUD_INDICATORS = "fraud_indicators"


@dataclass
class RiskFactor:
    """Individual risk factor"""
    category: RiskCategory
    factor_name: str
    weight: float
    score: float
    description: str
    evidence: Dict[str, Any]


@dataclass
class RiskAssessmentResult:
    """Complete risk assessment result"""
    customer_id: str
    overall_risk_score: float
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    recommendations: List[str]
    confidence_score: float
    assessment_timestamp: datetime


class AdvancedRiskScorer:
    """Advanced risk scoring system with multiple algorithms"""
    
    def __init__(self):
        # Risk weights by category (sum should equal 1.0)
        self.category_weights = {
            RiskCategory.IDENTITY_VERIFICATION: 0.25,
            RiskCategory.DOCUMENT_QUALITY: 0.20,
            RiskCategory.BEHAVIORAL_PATTERNS: 0.15,
            RiskCategory.GEOGRAPHIC_RISK: 0.15,
            RiskCategory.REGULATORY_COMPLIANCE: 0.15,
            RiskCategory.FRAUD_INDICATORS: 0.10
        }
        
        # High-risk countries (simplified list)
        self.high_risk_countries = {
            "AF", "BY", "CF", "CG", "CD", "CU", "ER", "GW", "HT", "IR", 
            "IQ", "KP", "LB", "LY", "ML", "MM", "NI", "PK", "SO", "SS", 
            "SD", "SY", "TR", "UA", "VE", "YE", "ZW"
        }
        
        # Sanctions lists (simplified)
        self.sanctions_keywords = [
            "taliban", "al-qaeda", "isis", "terrorist", "sanctions",
            "embargo", "frozen", "blocked", "designated"
        ]
    
    def assess_customer_risk(self, customer_id: str, session_context: Dict[str, Any] = None) -> RiskAssessmentResult:
        """Perform comprehensive risk assessment for a customer"""
        db = SessionLocal()
        
        try:
            customer_repo = get_customer_repo(db)
            document_repo = get_document_repo(db)
            
            # Get customer data
            customer = customer_repo.get_customer_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer not found: {customer_id}")
            
            # Get customer documents
            documents = document_repo.get_documents_by_customer_id(customer_id)
            
            # Initialize risk factors list
            risk_factors = []
            
            # 1. Identity Verification Risk
            identity_factors = self._assess_identity_verification(customer, documents, session_context)
            risk_factors.extend(identity_factors)
            
            # 2. Document Quality Risk
            document_factors = self._assess_document_quality(documents, session_context)
            risk_factors.extend(document_factors)
            
            # 3. Behavioral Patterns Risk
            behavioral_factors = self._assess_behavioral_patterns(customer, session_context)
            risk_factors.extend(behavioral_factors)
            
            # 4. Geographic Risk
            geographic_factors = self._assess_geographic_risk(customer)
            risk_factors.extend(geographic_factors)
            
            # 5. Regulatory Compliance Risk
            compliance_factors = self._assess_regulatory_compliance(customer, documents)
            risk_factors.extend(compliance_factors)
            
            # 6. Fraud Indicators
            fraud_factors = self._assess_fraud_indicators(customer, documents, session_context)
            risk_factors.extend(fraud_factors)
            
            # Calculate overall risk score
            overall_score = self._calculate_weighted_risk_score(risk_factors)
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_factors, risk_level)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(risk_factors)
            
            # Create assessment result
            result = RiskAssessmentResult(
                customer_id=customer_id,
                overall_risk_score=overall_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                recommendations=recommendations,
                confidence_score=confidence_score,
                assessment_timestamp=datetime.now(timezone.utc)
            )
            
            # Log risk assessment
            log_security_event(
                event_type="risk_assessment_completed",
                description=f"Risk assessment completed for customer: {customer_id}",
                severity=AuditLevel.INFO,
                additional_details={
                    "customer_id": customer_id,
                    "risk_score": overall_score,
                    "risk_level": risk_level.value,
                    "factors_count": len(risk_factors),
                    "confidence_score": confidence_score
                }
            )
            
            return result
            
        finally:
            db.close()
    
    def _assess_identity_verification(self, customer, documents, context: Dict[str, Any] = None) -> List[RiskFactor]:
        """Assess identity verification risks"""
        factors = []
        
        # Check for identity document presence
        id_docs = [doc for doc in documents if doc.document_type in ['passport', 'drivers_license', 'national_id']]
        
        if not id_docs:
            factors.append(RiskFactor(
                category=RiskCategory.IDENTITY_VERIFICATION,
                factor_name="missing_identity_document",
                weight=0.8,
                score=0.9,
                description="No identity documents provided",
                evidence={"document_count": len(documents), "id_document_count": 0}
            ))
        elif len(id_docs) == 1:
            factors.append(RiskFactor(
                category=RiskCategory.IDENTITY_VERIFICATION,
                factor_name="single_identity_document",
                weight=0.4,
                score=0.5,
                description="Only one identity document provided",
                evidence={"id_document_count": 1, "document_types": [doc.document_type for doc in id_docs]}
            ))
        
        # Check authenticity results from context
        if context and 'authenticity_results' in context:
            auth_results = context['authenticity_results'].get('results', [])
            failed_auth = [r for r in auth_results if not r.get('authentic', True)]
            
            if failed_auth:
                factors.append(RiskFactor(
                    category=RiskCategory.IDENTITY_VERIFICATION,
                    factor_name="document_authenticity_failure",
                    weight=0.9,
                    score=0.8,
                    description="Document authenticity verification failed",
                    evidence={"failed_documents": len(failed_auth), "total_documents": len(auth_results)}
                ))
        
        # Check PII consistency
        if context and 'pii_data' in context:
            pii_results = context['pii_data'].get('results', [])
            low_confidence_pii = []
            
            for pii_result in pii_results:
                confidence_scores = pii_result.get('confidence_scores', {})
                for field, confidence in confidence_scores.items():
                    if confidence < 0.7:
                        low_confidence_pii.append(f"{field}: {confidence}")
            
            if low_confidence_pii:
                factors.append(RiskFactor(
                    category=RiskCategory.IDENTITY_VERIFICATION,
                    factor_name="low_pii_confidence",
                    weight=0.6,
                    score=0.6,
                    description="Low confidence in PII extraction",
                    evidence={"low_confidence_fields": low_confidence_pii}
                ))
        
        return factors
    
    def _assess_document_quality(self, documents, context: Dict[str, Any] = None) -> List[RiskFactor]:
        """Assess document quality risks"""
        factors = []
        
        if not documents:
            factors.append(RiskFactor(
                category=RiskCategory.DOCUMENT_QUALITY,
                factor_name="no_documents",
                weight=1.0,
                score=1.0,
                description="No documents uploaded",
                evidence={"document_count": 0}
            ))
            return factors
        
        # Check document formats
        unsupported_formats = []
        small_files = []
        large_files = []
        
        for doc in documents:
            # Check file format
            if doc.mime_type not in ['application/pdf', 'image/jpeg', 'image/png']:
                unsupported_formats.append(doc.file_name)
            
            # Check file size
            if doc.file_size < 50000:  # Less than 50KB
                small_files.append(doc.file_name)
            elif doc.file_size > 20000000:  # More than 20MB
                large_files.append(doc.file_name)
        
        if unsupported_formats:
            factors.append(RiskFactor(
                category=RiskCategory.DOCUMENT_QUALITY,
                factor_name="unsupported_format",
                weight=0.5,
                score=0.6,
                description="Documents in unsupported formats",
                evidence={"unsupported_files": unsupported_formats}
            ))
        
        if small_files:
            factors.append(RiskFactor(
                category=RiskCategory.DOCUMENT_QUALITY,
                factor_name="small_file_size",
                weight=0.7,
                score=0.7,
                description="Documents with suspiciously small file sizes",
                evidence={"small_files": small_files}
            ))
        
        # Check document age (if available in context)
        if context and 'documents' in context:
            old_documents = []
            for doc_analysis in context['documents']:
                quality_score = doc_analysis.get('quality_score', 1.0)
                if quality_score < 0.5:
                    old_documents.append(doc_analysis.get('document_id'))
            
            if old_documents:
                factors.append(RiskFactor(
                    category=RiskCategory.DOCUMENT_QUALITY,
                    factor_name="poor_quality_documents",
                    weight=0.6,
                    score=0.6,
                    description="Documents with poor quality scores",
                    evidence={"poor_quality_docs": old_documents}
                ))
        
        return factors
    
    def _assess_behavioral_patterns(self, customer, context: Dict[str, Any] = None) -> List[RiskFactor]:
        """Assess behavioral pattern risks"""
        factors = []
        
        # Check customer registration time patterns
        registration_time = customer.created_at
        current_time = datetime.now(timezone.utc)
        
        # Check if registered during unusual hours (e.g., 2-6 AM)
        if 2 <= registration_time.hour <= 6:
            factors.append(RiskFactor(
                category=RiskCategory.BEHAVIORAL_PATTERNS,
                factor_name="unusual_registration_time",
                weight=0.3,
                score=0.4,
                description="Registration during unusual hours",
                evidence={"registration_hour": registration_time.hour}
            ))
        
        # Check rapid submission pattern
        time_since_registration = current_time - registration_time
        if time_since_registration < timedelta(minutes=5):
            factors.append(RiskFactor(
                category=RiskCategory.BEHAVIORAL_PATTERNS,
                factor_name="rapid_submission",
                weight=0.5,
                score=0.6,
                description="Very quick document submission after registration",
                evidence={"minutes_since_registration": time_since_registration.total_seconds() / 60}
            ))
        
        # Check email domain patterns
        email_domain = customer.email.split('@')[1].lower()
        suspicious_domains = ['tempmail.org', '10minutemail.com', 'guerrillamail.com', 'mailinator.com']
        
        if email_domain in suspicious_domains:
            factors.append(RiskFactor(
                category=RiskCategory.BEHAVIORAL_PATTERNS,
                factor_name="suspicious_email_domain",
                weight=0.8,
                score=0.8,
                description="Email from temporary/suspicious domain",
                evidence={"email_domain": email_domain}
            ))
        
        return factors
    
    def _assess_geographic_risk(self, customer) -> List[RiskFactor]:
        """Assess geographic risks"""
        factors = []
        
        if not customer.country:
            factors.append(RiskFactor(
                category=RiskCategory.GEOGRAPHIC_RISK,
                factor_name="unknown_country",
                weight=0.6,
                score=0.5,
                description="Customer country not specified",
                evidence={"country": None}
            ))
            return factors
        
        # Check against high-risk countries
        country_code = self._get_country_code(customer.country)
        
        if country_code in self.high_risk_countries:
            factors.append(RiskFactor(
                category=RiskCategory.GEOGRAPHIC_RISK,
                factor_name="high_risk_jurisdiction",
                weight=0.8,
                score=0.9,
                description="Customer from high-risk jurisdiction",
                evidence={"country": customer.country, "country_code": country_code}
            ))
        
        # Check for nationality mismatch
        if customer.nationality and customer.country:
            nationality_code = self._get_country_code(customer.nationality)
            if nationality_code != country_code:
                factors.append(RiskFactor(
                    category=RiskCategory.GEOGRAPHIC_RISK,
                    factor_name="nationality_country_mismatch",
                    weight=0.4,
                    score=0.3,
                    description="Mismatch between nationality and country of residence",
                    evidence={"nationality": customer.nationality, "country": customer.country}
                ))
        
        return factors
    
    def _assess_regulatory_compliance(self, customer, documents) -> List[RiskFactor]:
        """Assess regulatory compliance risks"""
        factors = []
        
        # Check age requirements (18+ for most jurisdictions)
        if customer.date_of_birth:
            age = (datetime.now().date() - customer.date_of_birth).days / 365.25
            if age < 18:
                factors.append(RiskFactor(
                    category=RiskCategory.REGULATORY_COMPLIANCE,
                    factor_name="underage_customer",
                    weight=1.0,
                    score=1.0,
                    description="Customer is under legal age",
                    evidence={"age": age, "date_of_birth": customer.date_of_birth.isoformat()}
                ))
            elif age > 100:
                factors.append(RiskFactor(
                    category=RiskCategory.REGULATORY_COMPLIANCE,
                    factor_name="unusual_age",
                    weight=0.6,
                    score=0.4,
                    description="Customer age seems unrealistic",
                    evidence={"age": age}
                ))
        else:
            factors.append(RiskFactor(
                category=RiskCategory.REGULATORY_COMPLIANCE,
                factor_name="missing_date_of_birth",
                weight=0.7,
                score=0.6,
                description="Date of birth not provided",
                evidence={"date_of_birth": None}
            ))
        
        # Check required fields completeness
        missing_fields = []
        required_fields = ['first_name', 'last_name', 'email', 'address_line_1', 'city', 'country']
        
        for field in required_fields:
            if not getattr(customer, field, None):
                missing_fields.append(field)
        
        if missing_fields:
            factors.append(RiskFactor(
                category=RiskCategory.REGULATORY_COMPLIANCE,
                factor_name="incomplete_customer_data",
                weight=0.5,
                score=len(missing_fields) * 0.1,
                description="Required customer data fields missing",
                evidence={"missing_fields": missing_fields}
            ))
        
        return factors
    
    def _assess_fraud_indicators(self, customer, documents, context: Dict[str, Any] = None) -> List[RiskFactor]:
        """Assess fraud indicator risks"""
        factors = []
        
        # Check for common fraud patterns in names
        suspicious_name_patterns = ['test', 'fake', 'dummy', 'anonymous', 'user', 'admin']
        full_name = f"{customer.first_name} {customer.last_name}".lower()
        
        for pattern in suspicious_name_patterns:
            if pattern in full_name:
                factors.append(RiskFactor(
                    category=RiskCategory.FRAUD_INDICATORS,
                    factor_name="suspicious_name_pattern",
                    weight=0.7,
                    score=0.8,
                    description="Name contains suspicious patterns",
                    evidence={"pattern": pattern, "full_name": full_name}
                ))
                break
        
        # Check for repeated characters in names
        if self._has_repeated_characters(customer.first_name) or self._has_repeated_characters(customer.last_name):
            factors.append(RiskFactor(
                category=RiskCategory.FRAUD_INDICATORS,
                factor_name="repeated_characters_name",
                weight=0.5,
                score=0.6,
                description="Name contains unusual repeated characters",
                evidence={"first_name": customer.first_name, "last_name": customer.last_name}
            ))
        
        # Check email patterns
        email_local = customer.email.split('@')[0].lower()
        if any(char * 3 in email_local for char in 'abcdefghijklmnopqrstuvwxyz0123456789'):
            factors.append(RiskFactor(
                category=RiskCategory.FRAUD_INDICATORS,
                factor_name="suspicious_email_pattern",
                weight=0.4,
                score=0.5,
                description="Email contains suspicious character patterns",
                evidence={"email": customer.email}
            ))
        
        return factors
    
    def _calculate_weighted_risk_score(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate weighted overall risk score"""
        category_scores = {category: [] for category in RiskCategory}
        
        # Group factors by category
        for factor in risk_factors:
            category_scores[factor.category].append(factor.weight * factor.score)
        
        # Calculate category averages
        category_averages = {}
        for category, scores in category_scores.items():
            if scores:
                category_averages[category] = sum(scores) / len(scores)
            else:
                category_averages[category] = 0.0
        
        # Calculate weighted overall score
        overall_score = 0.0
        for category, weight in self.category_weights.items():
            overall_score += weight * category_averages[category]
        
        return min(1.0, overall_score)
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from score"""
        if risk_score < 0.3:
            return RiskLevel.LOW
        elif risk_score < 0.7:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def _generate_recommendations(self, risk_factors: List[RiskFactor], risk_level: RiskLevel) -> List[str]:
        """Generate recommendations based on risk factors"""
        recommendations = []
        
        # High-level recommendations based on risk level
        if risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "Require manual review by senior analyst",
                "Request additional documentation",
                "Consider enhanced due diligence procedures",
                "Verify customer identity through alternative means"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "Assign to experienced analyst for review",
                "Verify suspicious findings",
                "Consider requesting additional documentation"
            ])
        else:
            recommendations.append("Proceed with standard processing")
        
        # Specific recommendations based on risk factors
        factor_categories = {factor.category for factor in risk_factors}
        
        if RiskCategory.IDENTITY_VERIFICATION in factor_categories:
            recommendations.append("Verify identity documents with issuing authorities")
        
        if RiskCategory.DOCUMENT_QUALITY in factor_categories:
            recommendations.append("Request higher quality document images")
        
        if RiskCategory.GEOGRAPHIC_RISK in factor_categories:
            recommendations.append("Apply enhanced due diligence for high-risk jurisdiction")
        
        if RiskCategory.FRAUD_INDICATORS in factor_categories:
            recommendations.append("Investigate potential fraud indicators")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_confidence_score(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate confidence score for the assessment"""
        if not risk_factors:
            return 0.5  # Medium confidence when no factors found
        
        # Base confidence on the number and quality of factors
        factor_count = len(risk_factors)
        high_weight_factors = len([f for f in risk_factors if f.weight > 0.7])
        
        # More factors and higher weights increase confidence
        confidence = min(1.0, 0.5 + (factor_count * 0.1) + (high_weight_factors * 0.1))
        
        return confidence
    
    def _get_country_code(self, country_name: str) -> str:
        """Get country code from country name (simplified mapping)"""
        country_codes = {
            "united states": "US", "usa": "US",
            "united kingdom": "GB", "uk": "GB",
            "canada": "CA", "germany": "DE", "france": "FR",
            "afghanistan": "AF", "belarus": "BY", "cuba": "CU",
            "iran": "IR", "iraq": "IQ", "north korea": "KP",
            "syria": "SY", "venezuela": "VE", "yemen": "YE"
        }
        
        return country_codes.get(country_name.lower(), country_name[:2].upper())
    
    def _has_repeated_characters(self, text: str) -> bool:
        """Check if text has unusual repeated character patterns"""
        if not text or len(text) < 3:
            return False
        
        # Check for 3+ consecutive repeated characters
        for i in range(len(text) - 2):
            if text[i] == text[i+1] == text[i+2]:
                return True
        
        return False


# Global risk scorer instance
risk_scorer = AdvancedRiskScorer()
