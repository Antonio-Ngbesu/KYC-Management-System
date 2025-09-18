"""
Test script to verify Azure Blob Storage setup with Azure Identity
"""
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from services.blob_storage import (
    blob_service_client, 
    KYC_DOC_CONTAINER, 
    KYC_PROCESSED_CONTAINER, 
    KYC_ARCHIVES_CONTAINER,
    ensure_containers_exist
)

def test_connection():
    """Test the connection to Azure Blob Storage"""
    try:
        # List all containers to test connection
        containers = blob_service_client.list_containers()
        print("✅ Successfully connected to Azure Blob Storage!")
        print("\nExisting containers:")
        for container in containers:
            print(f"  - {container.name}")
        
        print(f"\nRequired containers:")
        print(f"  - {KYC_DOC_CONTAINER}")
        print(f"  - {KYC_PROCESSED_CONTAINER}")
        print(f"  - {KYC_ARCHIVES_CONTAINER}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Azure Blob Storage: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're logged in to Azure CLI: az login")
        print("2. Check your storage account name in .env file")
        print("3. Ensure you have 'Storage Blob Data Contributor' role")
        return False

if __name__ == "__main__":
    print("Testing Azure Blob Storage Connection...")
    print("=" * 50)
    test_connection()
