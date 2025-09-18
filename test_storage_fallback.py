"""
Alternative test using connection string (fallback method)
"""
import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

def test_with_connection_string():
    """Test connection using connection string if available"""
    # Check if user has set up connection string as fallback
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    
    if connection_string:
        try:
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
            # Test connection
            containers = list(blob_service_client.list_containers())
            print("✅ Connected using connection string!")
            
            # Create containers if they don't exist
            required_containers = ["kyc-doc", "kyc-processed", "kyc-archives"]
            
            for container_name in required_containers:
                try:
                    container_client = blob_service_client.get_container_client(container_name)
                    if not container_client.exists():
                        container_client.create_container()
                        print(f"✅ Created container: {container_name}")
                    else:
                        print(f"✅ Container already exists: {container_name}")
                except Exception as e:
                    print(f"❌ Error with container {container_name}: {e}")
                    
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    else:
        print("❌ No connection string found in .env file")
        print("Add AZURE_STORAGE_CONNECTION_STRING to your .env file as backup")

if __name__ == "__main__":
    print("Testing with Connection String (Fallback)...")
    print("=" * 50)
    test_with_connection_string()
