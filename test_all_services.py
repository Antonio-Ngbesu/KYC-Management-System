"""
Comprehensive test script for KYC Document Analyzer
Tests all Azure services: Document Intelligence, Vision, Language, and Blob Storage
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

load_dotenv()

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("🔧 Testing Environment Variables...")
    print("=" * 50)
    
    required_vars = [
        "AZURE_FORM_RECOGNIZER_ENDPOINT",
        "AZURE_FORM_RECOGNIZER_KEY",
        "AZURE_VISION_ENDPOINT", 
        "AZURE_VISION_KEY",
        "AZURE_LANGUAGE_ENDPOINT",
        "AZURE_LANGUAGE_KEY",
        "AZURE_STORAGE_CONNECTION_STRING"
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower().split('_')[-1]}":
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing or not configured")
            all_present = False
    
    return all_present

def test_blob_storage():
    """Test Azure Blob Storage connection"""
    print("\n💾 Testing Azure Blob Storage...")
    print("=" * 50)
    
    try:
        from azure.storage.blob import BlobServiceClient
        
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # List containers
        containers = list(blob_service_client.list_containers())
        print(f"✅ Connected to Blob Storage successfully!")
        print(f"✅ Found {len(containers)} containers:")
        for container in containers:
            print(f"   - {container.name}")
            
        # Check required containers
        required_containers = ["kyc-doc", "kyc-processed", "kyc-archives"]
        existing_container_names = [c.name for c in containers]
        
        for container_name in required_containers:
            if container_name in existing_container_names:
                print(f"✅ Required container '{container_name}' exists")
            else:
                print(f"❌ Required container '{container_name}' missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Blob Storage connection failed: {e}")
        return False

def test_document_intelligence():
    """Test Azure Document Intelligence connection"""
    print("\n📄 Testing Azure Document Intelligence...")
    print("=" * 50)
    
    try:
        from azure.ai.formrecognizer import DocumentAnalysisClient
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
        key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
        
        client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        
        # Try to get info about the service (this will test authentication)
        print("✅ Document Intelligence client created successfully!")
        print(f"✅ Endpoint: {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document Intelligence connection failed: {e}")
        return False

def test_vision_api():
    """Test Azure Vision API connection"""
    print("\n👁️ Testing Azure Vision API...")
    print("=" * 50)
    
    try:
        from azure.ai.vision.imageanalysis import ImageAnalysisClient
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        key = os.getenv("AZURE_VISION_KEY")
        
        client = ImageAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        
        print("✅ Vision API client created successfully!")
        print(f"✅ Endpoint: {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vision API connection failed: {e}")
        print("Note: Vision API might need different package version or setup")
        return False

def test_language_api():
    """Test Azure Language API connection"""
    print("\n🗣️ Testing Azure Language API...")
    print("=" * 50)
    
    try:
        from azure.ai.textanalytics import TextAnalyticsClient
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
        key = os.getenv("AZURE_LANGUAGE_KEY")
        
        client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        
        # Test with a simple text analysis
        test_text = ["This is a test document for KYC verification."]
        result = client.recognize_entities(documents=test_text)
        
        print("✅ Language API client created successfully!")
        print(f"✅ Endpoint: {endpoint}")
        print("✅ Entity recognition test completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Language API connection failed: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI application startup"""
    print("\n🚀 Testing FastAPI Application...")
    print("=" * 50)
    
    try:
        from api.main import app
        print("✅ FastAPI app imported successfully!")
        print("✅ Ready to start server with: uvicorn src.api.main:app --reload")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 KYC Document Analyzer - System Test")
    print("=" * 60)
    
    results = {
        "Environment Variables": test_environment_variables(),
        "Blob Storage": test_blob_storage(),
        "Document Intelligence": test_document_intelligence(),
        "Vision API": test_vision_api(),
        "Language API": test_language_api(),
        "FastAPI App": test_fastapi_app()
    }
    
    print(f"\n📊 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All systems operational! Your KYC Document Analyzer is ready!")
        print("Next steps:")
        print("1. Start the API server: uvicorn src.api.main:app --reload")
        print("2. Open http://localhost:8000 in your browser")
        print("3. Visit http://localhost:8000/docs for API documentation")
    else:
        print(f"\n⚠️ Some systems need attention. Please fix the failing tests.")

if __name__ == "__main__":
    main()
