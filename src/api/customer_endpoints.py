"""
Customer management API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from auth.models import User, Permission
from auth.auth_service import get_current_user, require_permission, AuthenticationError, AuthorizationError
from models.customer_models import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerSearch,
    KYCStatusUpdate, CustomerStatistics, CustomerDetailResponse,
    CustomerListResponse, DocumentSummary, KYCSessionSummary
)
from services.customer_service import customer_service
from database.models import KYCStatus, RiskLevel

router = APIRouter(prefix="/customers", tags=["Customer Management"])


@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(require_permission(Permission.EDIT_CUSTOMER_DATA))
):
    """
    Create a new customer profile
    
    Requires permission: EDIT_CUSTOMER_DATA
    """
    try:
        customer_dict = customer_data.dict(exclude_unset=True)
        result = customer_service.create_customer(customer_dict, current_user.user_id)
        return CustomerResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create customer: {str(e)}")


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    query: Optional[str] = Query(None, description="Search query for name, email, or phone"),
    kyc_status: Optional[List[KYCStatus]] = Query(None, description="Filter by KYC status"),
    risk_level: Optional[List[RiskLevel]] = Query(None, description="Filter by risk level"),
    country: Optional[str] = Query(None, description="Filter by country"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Page size"),
    current_user: User = Depends(require_permission(Permission.VIEW_CUSTOMER_DATA))
):
    """
    List customers with optional filters and pagination
    
    Requires permission: VIEW_CUSTOMER_DATA
    """
    try:
        # Build filters
        filters = {}
        if kyc_status:
            filters['kyc_status'] = kyc_status
        if risk_level:
            filters['risk_level'] = risk_level
        if country:
            filters['country'] = country
        if is_active is not None:
            filters['is_active'] = is_active
        
        # Add pagination
        filters['limit'] = page_size
        filters['offset'] = (page - 1) * page_size
        
        # Search customers
        customers_data = customer_service.search_customers(
            query=query or "",
            filters=filters,
            requesting_user_id=current_user.user_id
        )
        
        # For this demo, we'll calculate pagination info
        # In production, you'd get this from the repository
        total_count = len(customers_data)  # This would be a separate count query
        has_next = len(customers_data) == page_size
        has_previous = page > 1
        
        customers = [CustomerResponse(**customer) for customer in customers_data]
        
        return CustomerListResponse(
            customers=customers,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list customers: {str(e)}")


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(
    customer_id: str = Path(..., description="Customer ID"),
    include_documents: bool = Query(True, description="Include customer documents"),
    include_sessions: bool = Query(True, description="Include KYC sessions"),
    current_user: User = Depends(require_permission(Permission.VIEW_CUSTOMER_DATA))
):
    """
    Get customer details by ID with optional related data
    
    Requires permission: VIEW_CUSTOMER_DATA
    """
    try:
        # Get customer basic info
        customer_data = customer_service.get_customer(customer_id, current_user.user_id)
        if not customer_data:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Build detailed response
        response_data = customer_data.copy()
        response_data['documents'] = []
        response_data['kyc_sessions'] = []
        response_data['total_documents'] = 0
        response_data['latest_session'] = None
        
        # Get documents if requested
        if include_documents:
            documents_data = customer_service.get_customer_documents(customer_id, current_user.user_id)
            response_data['documents'] = [DocumentSummary(**doc) for doc in documents_data]
            response_data['total_documents'] = len(documents_data)
        
        # Get KYC sessions if requested
        if include_sessions:
            sessions_data = customer_service.get_customer_kyc_sessions(customer_id, current_user.user_id)
            response_data['kyc_sessions'] = [KYCSessionSummary(**session) for session in sessions_data]
            if sessions_data:
                # Get latest session (assuming sorted by created_at desc)
                response_data['latest_session'] = KYCSessionSummary(**sessions_data[0])
        
        return CustomerDetailResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str = Path(..., description="Customer ID"),
    customer_updates: CustomerUpdate = ...,
    current_user: User = Depends(require_permission(Permission.EDIT_CUSTOMER_DATA))
):
    """
    Update customer information
    
    Requires permission: EDIT_CUSTOMER_DATA
    """
    try:
        updates = customer_updates.dict(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        result = customer_service.update_customer(customer_id, updates, current_user.user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return CustomerResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update customer: {str(e)}")


@router.patch("/{customer_id}/kyc-status", response_model=CustomerResponse)
async def update_kyc_status(
    customer_id: str = Path(..., description="Customer ID"),
    status_update: KYCStatusUpdate = ...,
    current_user: User = Depends(require_permission(Permission.EDIT_CUSTOMER_DATA))
):
    """
    Update customer KYC status
    
    Requires permission: EDIT_CUSTOMER_DATA
    """
    try:
        result = customer_service.update_kyc_status(
            customer_id=customer_id,
            new_status=status_update.status,
            updated_by_user_id=current_user.user_id,
            notes=status_update.notes
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return CustomerResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update KYC status: {str(e)}")


@router.get("/{customer_id}/documents", response_model=List[DocumentSummary])
async def get_customer_documents(
    customer_id: str = Path(..., description="Customer ID"),
    current_user: User = Depends(require_permission(Permission.VIEW_DOCUMENT))
):
    """
    Get all documents for a customer
    
    Requires permission: VIEW_DOCUMENT
    """
    try:
        documents_data = customer_service.get_customer_documents(customer_id, current_user.user_id)
        return [DocumentSummary(**doc) for doc in documents_data]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer documents: {str(e)}")


@router.get("/{customer_id}/kyc-sessions", response_model=List[KYCSessionSummary])
async def get_customer_kyc_sessions(
    customer_id: str = Path(..., description="Customer ID"),
    current_user: User = Depends(require_permission(Permission.VIEW_CUSTOMER_DATA))
):
    """
    Get all KYC sessions for a customer
    
    Requires permission: VIEW_CUSTOMER_DATA
    """
    try:
        sessions_data = customer_service.get_customer_kyc_sessions(customer_id, current_user.user_id)
        return [KYCSessionSummary(**session) for session in sessions_data]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer KYC sessions: {str(e)}")


@router.get("/statistics/dashboard", response_model=CustomerStatistics)
async def get_customer_statistics(
    current_user: User = Depends(require_permission(Permission.VIEW_ANALYTICS))
):
    """
    Get customer statistics for dashboard
    
    Requires permission: VIEW_ANALYTICS
    """
    try:
        stats = customer_service.get_customer_statistics(current_user.user_id)
        return CustomerStatistics(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer statistics: {str(e)}")


@router.post("/search", response_model=CustomerListResponse)
async def search_customers(
    search_params: CustomerSearch,
    current_user: User = Depends(require_permission(Permission.VIEW_CUSTOMER_DATA))
):
    """
    Advanced customer search with multiple filters
    
    Requires permission: VIEW_CUSTOMER_DATA
    """
    try:
        # Convert search params to filters
        filters = search_params.dict(exclude_unset=True, exclude={'query'})
        
        # Search customers
        customers_data = customer_service.search_customers(
            query=search_params.query or "",
            filters=filters,
            requesting_user_id=current_user.user_id
        )
        
        # Calculate pagination (simplified for demo)
        total_count = len(customers_data)
        page = (filters.get('offset', 0) // filters.get('limit', 50)) + 1
        page_size = filters.get('limit', 50)
        has_next = len(customers_data) == page_size
        has_previous = page > 1
        
        customers = [CustomerResponse(**customer) for customer in customers_data]
        
        return CustomerListResponse(
            customers=customers,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search customers: {str(e)}")
