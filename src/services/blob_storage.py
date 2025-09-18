import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure Blob Storage configuration
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
KYC_DOC_CONTAINER = os.getenv("AZURE_STORAGE_KYC_DOC_CONTAINER", "kyc-doc")
KYC_PROCESSED_CONTAINER = os.getenv("AZURE_STORAGE_KYC_PROCESSED_CONTAINER", "kyc-processed")
KYC_ARCHIVES_CONTAINER = os.getenv("AZURE_STORAGE_KYC_ARCHIVES_CONTAINER", "kyc-archives")

# Initialize BlobServiceClient using Azure Identity (more secure)
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url=f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=credential
)

def ensure_containers_exist():
    """
    Creates the required containers if they don't already exist.
    """
    containers = [KYC_DOC_CONTAINER, KYC_PROCESSED_CONTAINER, KYC_ARCHIVES_CONTAINER]
    
    for container_name in containers:
        try:
            container_client = blob_service_client.get_container_client(container_name)
            # Check if container exists, if not create it
            if not container_client.exists():
                container_client.create_container()
                print(f"Container '{container_name}' created successfully.")
            else:
                print(f"Container '{container_name}' already exists.")
        except Exception as e:
            print(f"Error creating container '{container_name}': {e}")

# Ensure containers exist when module is imported
ensure_containers_exist()

def upload_to_container(container_name, blob_name, file_path):
    """
    Uploads a file to the specified Azure Blob Storage container.

    :param container_name: Name of the container
    :param blob_name: Name of the blob (file) in the container
    :param file_path: Local path to the file to upload
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)
        with open(file_path, "rb") as data:
            container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        print(f"File {file_path} uploaded to container {container_name} as {blob_name}.")
    except Exception as e:
        print(f"Error uploading file to container {container_name}: {e}")

def download_from_container(container_name, blob_name, download_path):
    """
    Downloads a file from the specified Azure Blob Storage container.

    :param container_name: Name of the container
    :param blob_name: Name of the blob (file) in the container
    :param download_path: Local path to save the downloaded file
    """
    try:
        container_client = blob_service_client.get_container_client(container_name)
        with open(download_path, "wb") as file:
            blob_data = container_client.download_blob(blob_name)
            file.write(blob_data.readall())
        print(f"File {blob_name} downloaded from container {container_name} to {download_path}.")
    except Exception as e:
        print(f"Error downloading file from container {container_name}: {e}")

def move_blob(source_container, destination_container, blob_name):
    """
    Moves a blob from one container to another.

    :param source_container: Name of the source container
    :param destination_container: Name of the destination container
    :param blob_name: Name of the blob to move
    """
    try:
        source_blob = blob_service_client.get_blob_client(container=source_container, blob=blob_name)
        destination_blob = blob_service_client.get_blob_client(container=destination_container, blob=blob_name)

        # Copy blob to destination
        destination_blob.start_copy_from_url(source_blob.url)

        # Delete blob from source
        source_blob.delete_blob()

        print(f"Blob {blob_name} moved from {source_container} to {destination_container}.")
    except Exception as e:
        print(f"Error moving blob {blob_name} from {source_container} to {destination_container}: {e}")
