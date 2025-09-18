from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from models.kyc_models import (
    DocumentType, 
    DocumentMetadata, 
    UploadResponse,
    KYCSession,
    KYCStatus
)
from services.upload_service import upload_service
from auth.endpoints import router as auth_router
from database.config import init_database

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting KYC Document Analyzer...")
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Don't crash the app, but log the error
    
    yield
    
    # Shutdown
    print("👋 Shutting down KYC Document Analyzer...")

app = FastAPI(
    title="KYC Document Analyzer",
    description="API for analyzing and validating KYC documents using Azure AI services with database persistence and authentication",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")

# Import and include customer router
from api.customer_endpoints import router as customer_router
app.include_router(customer_router, prefix="/api/v1")

# Import and include workflow router
from api.workflow_endpoints import workflow_router
app.include_router(workflow_router)

@app.get("/")
async def root():
    return {
        "message": "KYC Document Analyzer API is running",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "upload": "/upload-document",
            "session": "/kyc-session/{customer_id}",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "KYC Document Analyzer",
        "timestamp": "2025-09-16T12:00:00Z"
    }

@app.post("/upload-document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    customer_id: str = Form(..., description="Customer ID"),
    document_type: DocumentType = Form(..., description="Type of document")
):
    """
    Upload a KYC document for processing
    
    - **file**: The document file (PDF, JPG, PNG)
    - **customer_id**: Unique identifier for the customer
    - **document_type**: Type of document (passport, drivers_license, etc.)
    """
    try:
        # Upload document
        metadata = await upload_service.upload_document(file, customer_id, document_type)
        
        return UploadResponse(
            success=True,
            message=f"Document uploaded successfully. Document ID: {metadata.document_id}",
            document_id=metadata.document_id,
            document_metadata=metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/document-types")
async def get_document_types():
    """Get list of supported document types"""
    return {
        "document_types": [
            {
                "value": doc_type.value,
                "name": doc_type.value.replace("_", " ").title(),
                "allowed_formats": ["PDF", "JPG", "PNG"]
            }
            for doc_type in DocumentType
        ]
    }

@app.get("/kyc-session/{customer_id}")
async def get_kyc_session(customer_id: str):
    """Get KYC session information for a customer"""
    # For now, return a mock session
    # In a real implementation, this would fetch from a database
    return {
        "session_id": f"session_{customer_id}",
        "customer_id": customer_id,
        "status": KYCStatus.PENDING.value,
        "created_timestamp": "2025-09-16T12:00:00Z",
        "documents": [],
        "message": "KYC session ready for document upload"
    }

@app.get("/containers/status")
async def check_containers():
    """Check status of Azure Blob Storage containers"""
    try:
        containers = list(upload_service.blob_service_client.list_containers())
        required_containers = ["kyc-doc", "kyc-processed", "kyc-archives"]
        
        container_status = {}
        for container_name in required_containers:
            exists = any(c.name == container_name for c in containers)
            container_status[container_name] = "active" if exists else "missing"
        
        return {
            "status": "ok",
            "containers": container_status,
            "total_containers": len(containers)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
