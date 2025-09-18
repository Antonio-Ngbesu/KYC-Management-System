"""
Real-time Notifications System
WebSocket-based notifications for status updates, alerts, and real-time communication
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

from database.config import SessionLocal
from database.repositories import get_kyc_session_repo, get_customer_repo
from utils.audit_logger import log_security_event, AuditLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications"""
    KYC_STATUS_UPDATE = "kyc_status_update"
    DOCUMENT_PROCESSED = "document_processed"
    RISK_ASSESSMENT_COMPLETE = "risk_assessment_complete"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    DECISION_MADE = "decision_made"
    SYSTEM_ALERT = "system_alert"
    USER_MESSAGE = "user_message"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification:
    """Notification message structure"""
    
    def __init__(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        recipient_id: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.type = notification_type
        self.title = title
        self.message = message
        self.recipient_id = recipient_id
        self.priority = priority
        self.data = data or {}
        self.timestamp = datetime.now(timezone.utc)
        self.read = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "recipient_id": self.recipient_id,
            "priority": self.priority.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read
        }


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # Store active connections by user ID
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store user metadata
        self.user_metadata: Dict[str, Dict[str, Any]] = {}
        # Store notification history
        self.notification_history: Dict[str, List[Notification]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, user_type: str = "customer"):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            self.notification_history[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.user_metadata[user_id] = {
            "user_type": user_type,
            "connected_at": datetime.now(timezone.utc),
            "last_activity": datetime.now(timezone.utc)
        }
        
        logger.info(f"User {user_id} ({user_type}) connected via WebSocket")
        
        # Send connection confirmation
        await self.send_personal_message(
            user_id,
            {
                "type": "connection_established",
                "message": "Real-time notifications connected",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Send any unread notifications
        await self.send_unread_notifications(user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_metadata:
                    del self.user_metadata[user_id]
        
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected_connections = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    
                    # Update last activity
                    if user_id in self.user_metadata:
                        self.user_metadata[user_id]["last_activity"] = datetime.now(timezone.utc)
                        
                except WebSocketDisconnect:
                    disconnected_connections.append(connection)
                except Exception as e:
                    logger.error(f"Error sending message to {user_id}: {e}")
                    disconnected_connections.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected_connections:
                self.disconnect(conn, user_id)
    
    async def send_notification(self, notification: Notification):
        """Send notification to user"""
        # Store notification in history
        if notification.recipient_id not in self.notification_history:
            self.notification_history[notification.recipient_id] = []
        
        self.notification_history[notification.recipient_id].append(notification)
        
        # Keep only last 100 notifications per user
        if len(self.notification_history[notification.recipient_id]) > 100:
            self.notification_history[notification.recipient_id] = \
                self.notification_history[notification.recipient_id][-100:]
        
        # Send to connected user
        await self.send_personal_message(
            notification.recipient_id,
            {
                "type": "notification",
                "notification": notification.to_dict()
            }
        )
        
        # Log notification
        log_security_event(
            event_type="notification_sent",
            description=f"Notification sent: {notification.title}",
            severity=AuditLevel.INFO,
            additional_details={
                "notification_id": notification.id,
                "recipient": notification.recipient_id,
                "type": notification.type.value,
                "priority": notification.priority.value
            }
        )
    
    async def send_unread_notifications(self, user_id: str):
        """Send all unread notifications to user"""
        if user_id in self.notification_history:
            unread_notifications = [
                n for n in self.notification_history[user_id] if not n.read
            ]
            
            if unread_notifications:
                await self.send_personal_message(
                    user_id,
                    {
                        "type": "unread_notifications",
                        "notifications": [n.to_dict() for n in unread_notifications],
                        "count": len(unread_notifications)
                    }
                )
    
    async def broadcast_system_message(self, message: Dict[str, Any], user_type: str = None):
        """Broadcast message to all connected users or specific user type"""
        for user_id, connections in self.active_connections.items():
            # Filter by user type if specified
            if user_type and self.user_metadata.get(user_id, {}).get("user_type") != user_type:
                continue
            
            await self.send_personal_message(user_id, message)
    
    def mark_notification_read(self, user_id: str, notification_id: str):
        """Mark notification as read"""
        if user_id in self.notification_history:
            for notification in self.notification_history[user_id]:
                if notification.id == notification_id:
                    notification.read = True
                    return True
        return False
    
    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notification history for user"""
        if user_id in self.notification_history:
            notifications = self.notification_history[user_id][-limit:]
            return [n.to_dict() for n in notifications]
        return []
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        user_types = {}
        
        for user_id, metadata in self.user_metadata.items():
            user_type = metadata.get("user_type", "unknown")
            user_types[user_type] = user_types.get(user_type, 0) + 1
        
        return {
            "total_users": len(self.active_connections),
            "total_connections": total_connections,
            "user_types": user_types,
            "active_users": list(self.active_connections.keys())
        }


# Global connection manager
connection_manager = ConnectionManager()


class NotificationService:
    """Service for creating and managing notifications"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def notify_kyc_status_update(
        self,
        customer_id: str,
        new_status: str,
        session_id: str,
        additional_info: str = ""
    ):
        """Notify customer of KYC status update"""
        status_messages = {
            "processing": "Your KYC application is being processed",
            "pending_review": "Your application is under manual review",
            "approved": "Congratulations! Your KYC application has been approved",
            "rejected": "Your KYC application requires additional information",
            "completed": "Your KYC verification is complete"
        }
        
        title = "KYC Status Update"
        message = status_messages.get(new_status, f"Status updated to: {new_status}")
        
        if additional_info:
            message += f". {additional_info}"
        
        priority = NotificationPriority.HIGH if new_status in ["approved", "rejected"] else NotificationPriority.MEDIUM
        
        notification = Notification(
            notification_type=NotificationType.KYC_STATUS_UPDATE,
            title=title,
            message=message,
            recipient_id=customer_id,
            priority=priority,
            data={
                "session_id": session_id,
                "new_status": new_status,
                "additional_info": additional_info
            }
        )
        
        await self.connection_manager.send_notification(notification)
    
    async def notify_document_processed(
        self,
        customer_id: str,
        document_name: str,
        status: str,
        issues: List[str] = None
    ):
        """Notify customer that document has been processed"""
        if status == "verified":
            title = "Document Verified"
            message = f"Your {document_name} has been successfully verified"
            priority = NotificationPriority.MEDIUM
        elif status == "failed":
            title = "Document Verification Failed"
            message = f"Issues found with your {document_name}. Please upload a new version."
            priority = NotificationPriority.HIGH
        else:
            title = "Document Processing Update"
            message = f"Your {document_name} is being processed"
            priority = NotificationPriority.LOW
        
        notification = Notification(
            notification_type=NotificationType.DOCUMENT_PROCESSED,
            title=title,
            message=message,
            recipient_id=customer_id,
            priority=priority,
            data={
                "document_name": document_name,
                "status": status,
                "issues": issues or []
            }
        )
        
        await self.connection_manager.send_notification(notification)
    
    async def notify_manual_review_required(
        self,
        analyst_id: str,
        customer_id: str,
        session_id: str,
        risk_level: str,
        reasons: List[str] = None
    ):
        """Notify analyst that manual review is required"""
        title = f"Manual Review Required - {risk_level.upper()} Risk"
        message = f"Customer {customer_id} requires manual review"
        
        if reasons:
            message += f". Reasons: {', '.join(reasons)}"
        
        notification = Notification(
            notification_type=NotificationType.MANUAL_REVIEW_REQUIRED,
            title=title,
            message=message,
            recipient_id=analyst_id,
            priority=NotificationPriority.HIGH if risk_level == "high" else NotificationPriority.MEDIUM,
            data={
                "customer_id": customer_id,
                "session_id": session_id,
                "risk_level": risk_level,
                "reasons": reasons or []
            }
        )
        
        await self.connection_manager.send_notification(notification)
    
    async def notify_decision_made(
        self,
        customer_id: str,
        decision: str,
        analyst_id: str,
        notes: str = ""
    ):
        """Notify customer of analyst decision"""
        decision_messages = {
            "approve": "Your KYC application has been approved!",
            "reject": "Your KYC application requires additional information",
            "request_more_info": "Please provide additional documentation"
        }
        
        title = "KYC Decision Update"
        message = decision_messages.get(decision, f"Decision: {decision}")
        
        if notes:
            message += f". Note from analyst: {notes}"
        
        priority = NotificationPriority.HIGH
        
        notification = Notification(
            notification_type=NotificationType.DECISION_MADE,
            title=title,
            message=message,
            recipient_id=customer_id,
            priority=priority,
            data={
                "decision": decision,
                "analyst_id": analyst_id,
                "notes": notes
            }
        )
        
        await self.connection_manager.send_notification(notification)
    
    async def notify_system_alert(
        self,
        admin_id: str,
        alert_type: str,
        alert_message: str,
        severity: str = "medium"
    ):
        """Notify admin of system alert"""
        title = f"System Alert - {alert_type.title()}"
        
        priority_map = {
            "low": NotificationPriority.LOW,
            "medium": NotificationPriority.MEDIUM,
            "high": NotificationPriority.HIGH,
            "urgent": NotificationPriority.URGENT
        }
        
        notification = Notification(
            notification_type=NotificationType.SYSTEM_ALERT,
            title=title,
            message=alert_message,
            recipient_id=admin_id,
            priority=priority_map.get(severity, NotificationPriority.MEDIUM),
            data={
                "alert_type": alert_type,
                "severity": severity
            }
        )
        
        await self.connection_manager.send_notification(notification)
    
    async def broadcast_maintenance_notice(
        self,
        message: str,
        scheduled_time: datetime,
        duration: str
    ):
        """Broadcast maintenance notice to all users"""
        await self.connection_manager.broadcast_system_message({
            "type": "maintenance_notice",
            "title": "Scheduled Maintenance",
            "message": message,
            "scheduled_time": scheduled_time.isoformat(),
            "duration": duration,
            "priority": "high"
        })


# Global notification service
notification_service = NotificationService(connection_manager)


# WebSocket endpoint
async def websocket_endpoint(websocket: WebSocket, user_id: str, user_type: str = "customer"):
    """WebSocket endpoint for real-time notifications"""
    await connection_manager.connect(websocket, user_id, user_type)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "mark_read":
                    notification_id = message.get("notification_id")
                    if notification_id:
                        success = connection_manager.mark_notification_read(user_id, notification_id)
                        await connection_manager.send_personal_message(
                            user_id,
                            {
                                "type": "mark_read_response",
                                "notification_id": notification_id,
                                "success": success
                            }
                        )
                
                elif message.get("type") == "get_notifications":
                    limit = message.get("limit", 50)
                    notifications = connection_manager.get_user_notifications(user_id, limit)
                    await connection_manager.send_personal_message(
                        user_id,
                        {
                            "type": "notifications_response",
                            "notifications": notifications
                        }
                    )
                
                elif message.get("type") == "ping":
                    await connection_manager.send_personal_message(
                        user_id,
                        {
                            "type": "pong",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user {user_id}")
            except Exception as e:
                logger.error(f"Error processing message from user {user_id}: {e}")
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        connection_manager.disconnect(websocket, user_id)


# HTML client for testing
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>KYC Notifications Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .notification { 
            background: #f0f0f0; 
            padding: 10px; 
            margin: 5px 0; 
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }
        .notification.high { border-left-color: #dc3545; }
        .notification.medium { border-left-color: #ffc107; }
        .notification.low { border-left-color: #28a745; }
        .controls { margin: 20px 0; }
        button { margin: 5px; padding: 10px; }
        input { margin: 5px; padding: 5px; }
        #status { font-weight: bold; }
        #messages { height: 400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; }
    </style>
</head>
<body>
    <h1>KYC Real-time Notifications Test</h1>
    
    <div class="controls">
        <input type="text" id="userId" placeholder="User ID" value="test-user-001">
        <select id="userType">
            <option value="customer">Customer</option>
            <option value="analyst">Analyst</option>
            <option value="admin">Admin</option>
        </select>
        <button onclick="connect()">Connect</button>
        <button onclick="disconnect()">Disconnect</button>
        <span id="status">Disconnected</span>
    </div>
    
    <div class="controls">
        <button onclick="getNotifications()">Get Notifications</button>
        <button onclick="sendPing()">Send Ping</button>
        <button onclick="clearMessages()">Clear Messages</button>
    </div>
    
    <div id="messages"></div>

    <script>
        let ws = null;
        
        function connect() {
            const userId = document.getElementById('userId').value;
            const userType = document.getElementById('userType').value;
            
            if (!userId) {
                alert('Please enter User ID');
                return;
            }
            
            ws = new WebSocket(`ws://localhost:8000/api/v1/notifications/ws/${userId}?user_type=${userType}`);
            
            ws.onopen = function(event) {
                document.getElementById('status').textContent = 'Connected';
                document.getElementById('status').style.color = 'green';
                addMessage('Connected to notification service', 'info');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addMessage(JSON.stringify(data, null, 2), 'message');
                
                if (data.type === 'notification') {
                    showNotification(data.notification);
                }
            };
            
            ws.onclose = function(event) {
                document.getElementById('status').textContent = 'Disconnected';
                document.getElementById('status').style.color = 'red';
                addMessage('Disconnected from notification service', 'error');
            };
            
            ws.onerror = function(error) {
                addMessage('WebSocket error: ' + error, 'error');
            };
        }
        
        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
        }
        
        function getNotifications() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'get_notifications',
                    limit: 20
                }));
            }
        }
        
        function sendPing() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'ping'
                }));
            }
        }
        
        function showNotification(notification) {
            const notificationDiv = document.createElement('div');
            notificationDiv.className = `notification ${notification.priority}`;
            notificationDiv.innerHTML = `
                <strong>${notification.title}</strong><br>
                ${notification.message}<br>
                <small>Priority: ${notification.priority} | Time: ${notification.timestamp}</small>
            `;
            
            document.getElementById('messages').appendChild(notificationDiv);
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }
        
        function addMessage(message, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.innerHTML = `<pre>${message}</pre>`;
            
            document.getElementById('messages').appendChild(messageDiv);
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }
        
        function clearMessages() {
            document.getElementById('messages').innerHTML = '';
        }
    </script>
</body>
</html>
"""


def get_notification_test_page():
    """Get HTML test page for notifications"""
    return HTMLResponse(content=html_content)


# Export components
__all__ = [
    "NotificationType",
    "NotificationPriority", 
    "Notification",
    "ConnectionManager",
    "NotificationService",
    "connection_manager",
    "notification_service",
    "websocket_endpoint",
    "get_notification_test_page"
]
