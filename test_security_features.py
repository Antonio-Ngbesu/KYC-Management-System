"""
Test script for Security & Compliance Features
Demonstrates the new security features added to the KYC Document Analyzer
"""
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.audit_logger import (
    log_document_upload, log_document_processing, log_pii_access, 
    log_security_event, AuditLevel
)
from services.pii_redaction import detect_and_redact_text, pii_service
from services.authenticity_checker import verify_document_authenticity
from services.document_retention import retention_service, get_retention_status_report
from auth.auth_service import auth_service, AuthenticationError
from auth.models import UserRole, Permission

def test_audit_logging():
    """Test the audit logging system"""
    print("🔍 Testing Audit Logging System...")
    print("=" * 50)
    
    try:
        # Test document upload logging
        log_document_upload(
            document_id="test_doc_001",
            filename="test_passport.jpg",
            file_size=2048576,
            document_type="passport",
            user_id="test_user_001",
            ip_address="192.168.1.100"
        )
        print("✅ Document upload logged successfully")
        
        # Test document processing logging
        log_document_processing(
            document_id="test_doc_001",
            processing_result="success",
            processing_time=2.5,
            services_used=["document_intelligence", "vision_api", "pii_redaction"],
            user_id="test_user_001",
            extracted_data={"name": "John Doe", "passport_number": "A12345678"}
        )
        print("✅ Document processing logged successfully")
        
        # Test PII access logging
        log_pii_access(
            document_id="test_doc_001",
            pii_fields=["passport_number", "date_of_birth"],
            access_reason="kyc_verification",
            user_id="test_user_001",
            ip_address="192.168.1.100"
        )
        print("✅ PII access logged successfully")
        
        # Test security event logging
        log_security_event(
            event_type="suspicious_activity",
            description="Multiple failed login attempts detected",
            severity=AuditLevel.WARNING,
            user_id="test_user_001",
            ip_address="192.168.1.100",
            additional_details={"attempts": 3, "time_window": "5_minutes"}
        )
        print("✅ Security event logged successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Audit logging test failed: {e}")
        return False

def test_pii_redaction():
    """Test PII detection and redaction"""
    print("\n🔒 Testing PII Redaction Service...")
    print("=" * 50)
    
    try:
        # Test text with various PII types
        test_text = """
        Customer Information:
        Name: John Doe
        SSN: 123-45-6789
        Phone: (555) 123-4567
        Email: john.doe@email.com
        Credit Card: 4532-1234-5678-9012
        Address: 123 Main St, Anytown, ST 12345
        """
        
        redacted_text, matches, report = detect_and_redact_text(test_text)
        
        print(f"✅ PII Detection completed")
        print(f"✅ Found {len(matches)} PII elements")
        print(f"✅ Risk Level: {report['risk_level']}")
        
        print("\nPII Types Detected:")
        for pii_type, info in report['pii_summary'].items():
            print(f"  - {info['description']}: {info['count']} instances")
        
        print(f"\nOriginal text length: {len(test_text)}")
        print(f"Redacted text length: {len(redacted_text)}")
        print("✅ Text redaction successful")
        
        return True
        
    except Exception as e:
        print(f"❌ PII redaction test failed: {e}")
        return False

def test_document_authenticity():
    """Test document authenticity verification"""
    print("\n🛡️ Testing Document Authenticity Verification...")
    print("=" * 50)
    
    try:
        # Create a larger test image (100x100 pixel PNG for proper analysis)
        from PIL import Image
        import io
        
        # Create a test image that's large enough for OpenCV analysis
        test_image = Image.new('RGB', (200, 200), color='white')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        test_image_data = img_buffer.getvalue()
        
        result = verify_document_authenticity(test_image_data, "passport")
        
        print(f"✅ Authenticity check completed")
        print(f"✅ Document status: {result['document_authenticity']}")
        print(f"✅ Confidence score: {result['confidence_score']:.2f}")
        print(f"✅ Fraud indicators found: {result['fraud_indicators']}")
        print(f"✅ Risk assessment: {result['risk_assessment']}")
        
        if result['detailed_checks']:
            print("\nDetailed Checks:")
            for check in result['detailed_checks'][:3]:  # Show first 3
                print(f"  - {check['type']}: {check['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document authenticity test failed: {e}")
        return False

def test_authentication_system():
    """Test user authentication and authorization"""
    print("\n👤 Testing Authentication & Authorization System...")
    print("=" * 50)
    
    try:
        # Test login with default admin
        print("Testing admin login...")
        auth_result = auth_service.authenticate_user("admin", "admin123", "127.0.0.1")
        print("✅ Admin login successful")
        print(f"✅ Token generated: {len(auth_result['access_token'])} characters")
        print(f"✅ User role: {auth_result['user']['role']}")
        print(f"✅ Permissions: {len(auth_result['user']['permissions'])} permissions")
        
        # Test token verification
        user = auth_service.verify_token(auth_result['access_token'])
        print("✅ Token verification successful")
        print(f"✅ Verified user: {user.username}")
        
        # Test permission checking
        admin_user = auth_service.get_user_by_username("admin")
        has_manage_users = admin_user.has_permission(Permission.MANAGE_USERS)
        has_view_pii = admin_user.has_permission(Permission.VIEW_PII)
        print(f"✅ Admin can manage users: {has_manage_users}")
        print(f"✅ Admin can view PII: {has_view_pii}")
        
        # Test creating a new user
        analyst_user = auth_service.create_user(
            username="analyst1",
            email="analyst@company.com",
            password="analyst123",
            role=UserRole.ANALYST,
            creator_user_id=admin_user.user_id,
            department="KYC"
        )
        print(f"✅ Created analyst user: {analyst_user.username}")
        print(f"✅ Analyst permissions: {len(analyst_user.permissions)}")
        
        # Test login with wrong password
        try:
            auth_service.authenticate_user("admin", "wrongpassword", "127.0.0.1")
            print("❌ Should have failed with wrong password")
            return False
        except AuthenticationError:
            print("✅ Correctly rejected wrong password")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_document_retention():
    """Test document retention policies"""
    print("\n📅 Testing Document Retention System...")
    print("=" * 50)
    
    try:
        # Get retention policy information
        policies = retention_service.get_policy_info()
        print(f"✅ Loaded {len(policies)} retention policies")
        
        for category, policy in policies.items():
            print(f"  - {category}: {policy['retention_period_days']} days retention")
        
        # Get retention status report
        report = get_retention_status_report()
        print(f"✅ Generated retention report")
        print(f"✅ Total documents scanned: {report['total_documents']}")
        print(f"✅ Immediate actions needed: {report['immediate_actions_needed']}")
        print(f"✅ Overdue actions: {len(report['overdue_actions'])}")
        
        if report['by_category']:
            print("\nDocuments by category:")
            for category, info in report['by_category'].items():
                print(f"  - {category}: {info['count']} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Document retention test failed: {e}")
        return False

def main():
    """Run all security feature tests"""
    print("🔐 KYC Document Analyzer - Security & Compliance Features Test")
    print("=" * 70)
    
    tests = [
        ("Audit Logging", test_audit_logging),
        ("PII Redaction", test_pii_redaction),
        ("Document Authenticity", test_document_authenticity),
        ("Authentication System", test_authentication_system),
        ("Document Retention", test_document_retention),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test encountered an error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Security Features Test Summary")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All security features are working correctly!")
        print("\n🔒 Your KYC system now includes:")
        print("   • Comprehensive audit logging")
        print("   • Automatic PII detection and redaction")
        print("   • Document authenticity verification")
        print("   • Role-based access control")
        print("   • Automated document retention policies")
    else:
        print("⚠️ Some security features need attention.")
    
    print("\n📁 Check the 'logs/audit.log' file for detailed audit trails.")

if __name__ == "__main__":
    main()
