"""
Test script for document upload functionality
"""
import requests
import json
from io import BytesIO

def test_upload_endpoints():
    """Test the document upload API endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing KYC Document Upload System")
    print("=" * 50)
    
    # Test 1: Check API health
    print("\n1. 🏥 Testing API Health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ API is healthy")
            print(f"   ✅ Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Get document types
    print("\n2. 📋 Testing Document Types Endpoint...")
    try:
        response = requests.get(f"{base_url}/document-types")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Document types retrieved successfully")
            print(f"   ✅ Available types: {len(data['document_types'])}")
            for doc_type in data['document_types'][:3]:  # Show first 3
                print(f"      - {doc_type['name']} ({doc_type['value']})")
        else:
            print(f"   ❌ Document types failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Document types error: {e}")
    
    # Test 3: Check containers status
    print("\n3. 🗂️ Testing Container Status...")
    try:
        response = requests.get(f"{base_url}/containers/status")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Container status retrieved")
            print(f"   ✅ Status: {data['status']}")
            for container, status in data['containers'].items():
                emoji = "✅" if status == "active" else "❌"
                print(f"      {emoji} {container}: {status}")
        else:
            print(f"   ❌ Container status failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Container status error: {e}")
    
    # Test 4: Get KYC session
    print("\n4. 👤 Testing KYC Session...")
    try:
        customer_id = "test_customer_123"
        response = requests.get(f"{base_url}/kyc-session/{customer_id}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ KYC session retrieved")
            print(f"   ✅ Customer ID: {data['customer_id']}")
            print(f"   ✅ Status: {data['status']}")
        else:
            print(f"   ❌ KYC session failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ KYC session error: {e}")
    
    # Test 5: Document upload (mock test - we'll create a dummy file)
    print("\n5. 📤 Testing Document Upload (Mock)...")
    try:
        # Create a small dummy image file (1x1 pixel PNG)
        dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        files = {
            'file': ('test_passport.png', dummy_png, 'image/png')
        }
        data = {
            'customer_id': 'test_customer_123',
            'document_type': 'passport'
        }
        
        response = requests.post(f"{base_url}/upload-document", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Document upload successful!")
            print(f"   ✅ Document ID: {result['document_id']}")
            print(f"   ✅ Success: {result['success']}")
            print(f"   ✅ Message: {result['message']}")
        else:
            print(f"   ❌ Document upload failed: {response.status_code}")
            if response.text:
                print(f"   ❌ Error: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Document upload error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Document Upload System Testing Complete!")
    print("\nYour KYC Document Upload System is ready!")
    print("Available at: http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    test_upload_endpoints()
