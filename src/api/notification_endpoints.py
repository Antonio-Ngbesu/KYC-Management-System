"""
Notification API Endpoints
REST and WebSocket endpoints for real-time notifications
"""
from fastapi import APIRouter, WebSocket, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.notification_service import (
    connection_manager,
    notification_service,
    websocket_endpoint,
    get_notification_test_page,
    NotificationType,
    NotificationPriority,
    Notification
)
from api.auth import get_current_user, verify_admin_role


# Request/Response Models
class SendNotificationRequest(BaseModel):
    recipient_id: str = Field(..., description="User ID to send notification to")
    notification_type: str = Field(..., description="Type of notification")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: str = Field(default="medium", description="Notification priority")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    recipient_id: str
    priority: str
    data: Dict[str, Any]
    timestamp: datetime
    read: bool


class ConnectionStatsResponse(BaseModel):
    total_users: int
    total_connections: int
    user_types: Dict[str, int]
    active_users: List[str]


class BroadcastMessageRequest(BaseModel):
    title: str = Field(..., description="Message title")
    message: str = Field(..., description="Message content")
    user_type: Optional[str] = Field(default=None, description="Target user type (customer, analyst, admin)")
    priority: str = Field(default="medium", description="Message priority")


# Router setup
notification_router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@notification_router.websocket("/ws/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str,
    user_type: str = Query(default="customer", description="User type (customer, analyst, admin)")
):
    """WebSocket endpoint for real-time notifications"""
    await websocket_endpoint(websocket, user_id, user_type)


@notification_router.get("/test", response_class=HTMLResponse)
async def get_test_page():
    """Get HTML test page for WebSocket notifications"""
    return get_notification_test_page()


@notification_router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user = Depends(get_current_user)
):
    """Send a notification to a specific user"""
    try:
        # Validate notification type
        try:
            notification_type = NotificationType(request.notification_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid notification type: {request.notification_type}")
        
        # Validate priority
        try:
            priority = NotificationPriority(request.priority)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {request.priority}")
        
        # Create notification
        notification = Notification(
            notification_type=notification_type,
            title=request.title,
            message=request.message,
            recipient_id=request.recipient_id,
            priority=priority,
            data=request.data or {}
        )
        
        # Send notification
        await connection_manager.send_notification(notification)
        
        return {
            "success": True,
            "message": "Notification sent successfully",
            "notification_id": notification.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


@notification_router.get("/user/{user_id}", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Get notification history for a user"""
    try:
        # Check if user can access these notifications
        if current_user.id != user_id and current_user.role not in ['admin', 'analyst']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        notifications = connection_manager.get_user_notifications(user_id, limit)
        
        return [
            NotificationResponse(
                id=notif["id"],
                type=notif["type"],
                title=notif["title"],
                message=notif["message"],
                recipient_id=notif["recipient_id"],
                priority=notif["priority"],
                data=notif["data"],
                timestamp=datetime.fromisoformat(notif["timestamp"]),
                read=notif["read"]
            )
            for notif in notifications
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")


@notification_router.put("/mark-read/{notification_id}")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Query(..., description="User ID"),
    current_user = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        # Check if user can mark this notification as read
        if current_user.id != user_id and current_user.role not in ['admin']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = connection_manager.mark_notification_read(user_id, notification_id)
        
        if success:
            return {
                "success": True,
                "message": "Notification marked as read"
            }
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")


@notification_router.get("/stats", response_model=ConnectionStatsResponse)
async def get_connection_stats(
    current_user = Depends(get_current_user)
):
    """Get WebSocket connection statistics (admin only)"""
    verify_admin_role(current_user)
    
    try:
        stats = connection_manager.get_connection_stats()
        
        return ConnectionStatsResponse(
            total_users=stats["total_users"],
            total_connections=stats["total_connections"],
            user_types=stats["user_types"],
            active_users=stats["active_users"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connection stats: {str(e)}")


@notification_router.post("/broadcast")
async def broadcast_message(
    request: BroadcastMessageRequest,
    current_user = Depends(get_current_user)
):
    """Broadcast message to all users or specific user type (admin only)"""
    verify_admin_role(current_user)
    
    try:
        message = {
            "type": "broadcast_message",
            "title": request.title,
            "message": request.message,
            "priority": request.priority,
            "timestamp": datetime.utcnow().isoformat(),
            "sender": current_user.username
        }
        
        await connection_manager.broadcast_system_message(message, request.user_type)
        
        return {
            "success": True,
            "message": f"Message broadcasted to {request.user_type or 'all'} users"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast message: {str(e)}")


@notification_router.post("/kyc-status-update")
async def notify_kyc_status_update(
    customer_id: str,
    new_status: str,
    session_id: str,
    additional_info: str = "",
    current_user = Depends(get_current_user)
):
    """Send KYC status update notification"""
    try:
        await notification_service.notify_kyc_status_update(
            customer_id=customer_id,
            new_status=new_status,
            session_id=session_id,
            additional_info=additional_info
        )
        
        return {
            "success": True,
            "message": "KYC status update notification sent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send KYC status update: {str(e)}")


@notification_router.post("/document-processed")
async def notify_document_processed(
    customer_id: str,
    document_name: str,
    status: str,
    issues: Optional[List[str]] = None,
    current_user = Depends(get_current_user)
):
    """Send document processing notification"""
    try:
        await notification_service.notify_document_processed(
            customer_id=customer_id,
            document_name=document_name,
            status=status,
            issues=issues or []
        )
        
        return {
            "success": True,
            "message": "Document processing notification sent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send document processing notification: {str(e)}")


@notification_router.post("/manual-review-required")
async def notify_manual_review_required(
    analyst_id: str,
    customer_id: str,
    session_id: str,
    risk_level: str,
    reasons: Optional[List[str]] = None,
    current_user = Depends(get_current_user)
):
    """Send manual review required notification"""
    try:
        await notification_service.notify_manual_review_required(
            analyst_id=analyst_id,
            customer_id=customer_id,
            session_id=session_id,
            risk_level=risk_level,
            reasons=reasons or []
        )
        
        return {
            "success": True,
            "message": "Manual review notification sent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send manual review notification: {str(e)}")


@notification_router.post("/decision-made")
async def notify_decision_made(
    customer_id: str,
    decision: str,
    analyst_id: str,
    notes: str = "",
    current_user = Depends(get_current_user)
):
    """Send decision made notification"""
    try:
        await notification_service.notify_decision_made(
            customer_id=customer_id,
            decision=decision,
            analyst_id=analyst_id,
            notes=notes
        )
        
        return {
            "success": True,
            "message": "Decision notification sent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send decision notification: {str(e)}")


@notification_router.post("/system-alert")
async def notify_system_alert(
    admin_id: str,
    alert_type: str,
    alert_message: str,
    severity: str = "medium",
    current_user = Depends(get_current_user)
):
    """Send system alert notification (admin only)"""
    verify_admin_role(current_user)
    
    try:
        await notification_service.notify_system_alert(
            admin_id=admin_id,
            alert_type=alert_type,
            alert_message=alert_message,
            severity=severity
        )
        
        return {
            "success": True,
            "message": "System alert notification sent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send system alert: {str(e)}")


@notification_router.post("/maintenance-notice")
async def broadcast_maintenance_notice(
    message: str,
    scheduled_time: datetime,
    duration: str,
    current_user = Depends(get_current_user)
):
    """Broadcast maintenance notice (admin only)"""
    verify_admin_role(current_user)
    
    try:
        await notification_service.broadcast_maintenance_notice(
            message=message,
            scheduled_time=scheduled_time,
            duration=duration
        )
        
        return {
            "success": True,
            "message": "Maintenance notice broadcasted"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast maintenance notice: {str(e)}")


@notification_router.delete("/user/{user_id}/notifications")
async def clear_user_notifications(
    user_id: str,
    current_user = Depends(get_current_user)
):
    """Clear all notifications for a user"""
    try:
        # Check permissions
        if current_user.id != user_id and current_user.role not in ['admin']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Clear notifications (reset the list)
        if user_id in connection_manager.notification_history:
            connection_manager.notification_history[user_id] = []
        
        return {
            "success": True,
            "message": "All notifications cleared"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear notifications: {str(e)}")


# Export router
__all__ = ["notification_router"]
