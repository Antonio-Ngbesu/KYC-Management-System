"""
Admin Dashboard - System Management Interface
Comprehensive admin interface for system management, user administration, and analytics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any
import requests
import io

# Configure Streamlit
st.set_page_config(
    page_title="KYC Admin Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern admin interface
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global app styling */
    .stApp {
        background: linear-gradient(135deg, #6a1b9a 0%, #8e24aa 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        margin: 2rem auto;
    }
    
    /* Header styling */
    .admin-header {
        background: linear-gradient(135deg, #6a1b9a 0%, #8e24aa 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 3rem;
        text-align: center;
        box-shadow: 0 15px 35px rgba(106, 27, 154, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .admin-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: admin-pulse 6s ease-in-out infinite;
    }
    
    @keyframes admin-pulse {
        0%, 100% { opacity: 0.3; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(1.1); }
    }
    
    .admin-header h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.8rem;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        position: relative;
        z-index: 1;
    }
    
    /* Admin cards */
    .admin-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border: 2px solid #e1e8ed;
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .admin-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #6a1b9a, #8e24aa);
    }
    
    .admin-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        border-color: #8e24aa;
    }
    
    /* Status indicators */
    .status-healthy { 
        color: #4caf50; 
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        text-shadow: 0 1px 2px rgba(76, 175, 80, 0.3);
    }
    
    .status-warning { 
        color: #ff9800; 
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        text-shadow: 0 1px 2px rgba(255, 152, 0, 0.3);
    }
    
    .status-error { 
        color: #f44336; 
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        text-shadow: 0 1px 2px rgba(244, 67, 54, 0.3);
    }
    
    /* System metrics */
    .system-metric {
        background: linear-gradient(135deg, #ffffff 0%, #f3e5f5 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem;
        border: 2px solid #e1bee7;
        box-shadow: 0 8px 25px rgba(106, 27, 154, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .system-metric::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #6a1b9a, #8e24aa);
    }
    
    .system-metric:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(106, 27, 154, 0.2);
    }
    
    .system-metric h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .system-metric .metric-value {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #6a1b9a;
        margin-bottom: 0.5rem;
    }
    
    /* User rows */
    .user-row {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 15px;
        border-left: 5px solid #6a1b9a;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .user-row:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        border-left-color: #8e24aa;
    }
    
    /* Alert styles */
    .alert-high { 
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border-left: 5px solid #f44336;
        box-shadow: 0 4px 15px rgba(244, 67, 54, 0.15);
    }
    
    .alert-medium { 
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 5px solid #ff9800;
        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.15);
    }
    
    .alert-info { 
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 5px solid #2196f3;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.15);
    }
    
    /* Configuration sections */
    .config-section {
        background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    .config-section h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6a1b9a 0%, #8e24aa 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(106, 27, 154, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(106, 27, 154, 0.4);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

class AdminAPI:
    """API client for admin operations"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "status": "healthy",
            "uptime": "15d 8h 32m",
            "version": "2.0.0",
            "last_deployment": "2025-09-15T14:30:00Z",
            "services": {
                "api": {"status": "healthy", "response_time": "45ms"},
                "database": {"status": "healthy", "connections": 23},
                "workflow_engine": {"status": "healthy", "active_sessions": 67},
                "ai_services": {"status": "healthy", "quota_used": "67%"},
                "storage": {"status": "healthy", "usage": "234GB/500GB"}
            }
        }
    
    def get_user_management_data(self) -> List[Dict[str, Any]]:
        """Get user management data"""
        return [
            {
                "id": "user-001",
                "username": "admin@company.com",
                "role": "admin",
                "status": "active",
                "last_login": "2025-09-17T09:15:00Z",
                "created_at": "2025-08-01T10:00:00Z"
            },
            {
                "id": "user-002", 
                "username": "analyst1@company.com",
                "role": "senior_analyst",
                "status": "active",
                "last_login": "2025-09-17T08:45:00Z",
                "created_at": "2025-08-15T14:20:00Z"
            },
            {
                "id": "user-003",
                "username": "analyst2@company.com", 
                "role": "analyst",
                "status": "inactive",
                "last_login": "2025-09-15T16:30:00Z",
                "created_at": "2025-09-01T11:10:00Z"
            }
        ]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        return {
            "applications": {
                "total": 2847,
                "today": 156,
                "pending": 89,
                "processing": 34,
                "completed": 2724
            },
            "performance": {
                "avg_processing_time": "18.5 minutes",
                "api_response_time": "45ms",
                "success_rate": "99.2%",
                "uptime": "99.8%"
            },
            "storage": {
                "documents": "234GB",
                "database": "45GB", 
                "logs": "12GB",
                "backups": "67GB"
            }
        }
    
    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get system audit logs"""
        return [
            {
                "timestamp": "2025-09-17T10:45:23Z",
                "event_type": "user_login",
                "user": "analyst1@company.com",
                "severity": "info",
                "details": "Successful login from IP 192.168.1.100"
            },
            {
                "timestamp": "2025-09-17T10:42:11Z", 
                "event_type": "kyc_workflow_completed",
                "user": "system",
                "severity": "info",
                "details": "KYC workflow kyc-001 completed successfully"
            },
            {
                "timestamp": "2025-09-17T10:35:45Z",
                "event_type": "document_upload",
                "user": "customer@example.com",
                "severity": "info", 
                "details": "Document uploaded: passport.pdf"
            },
            {
                "timestamp": "2025-09-17T10:30:12Z",
                "event_type": "risk_assessment_high",
                "user": "system",
                "severity": "warning",
                "details": "High risk customer detected: cust-001"
            }
        ]
    
    def get_system_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts"""
        return [
            {
                "id": "alert-001",
                "severity": "high",
                "type": "security",
                "message": "Multiple failed login attempts detected",
                "timestamp": "2025-09-17T10:15:00Z",
                "resolved": False
            },
            {
                "id": "alert-002",
                "severity": "medium", 
                "type": "performance",
                "message": "API response time above threshold (>100ms)",
                "timestamp": "2025-09-17T09:30:00Z",
                "resolved": False
            },
            {
                "id": "alert-003",
                "severity": "info",
                "type": "system",
                "message": "Scheduled backup completed successfully",
                "timestamp": "2025-09-17T02:00:00Z",
                "resolved": True
            }
        ]

# Initialize API client
api_client = AdminAPI(API_BASE_URL)

def init_session_state():
    """Initialize session state"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'admin_username' not in st.session_state:
        st.session_state.admin_username = "System Administrator"

def show_header():
    """Display admin dashboard header"""
    st.markdown("""
    <div class="admin-header">
        <h1>⚙️ KYC Admin Dashboard</h1>
        <p>System Management & Administration Console</p>
    </div>
    """, unsafe_allow_html=True)

def show_login():
    """Show admin login"""
    st.markdown("### 🔐 Administrator Authentication")
    
    with st.form("admin_login"):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            username = st.text_input("Username", placeholder="admin@company.com")
            password = st.text_input("Password", type="password")
        
        with col2:
            two_factor = st.text_input("2FA Code", placeholder="Enter 6-digit code")
            remember_me = st.checkbox("Remember this device")
        
        if st.form_submit_button("🔓 Authenticate", use_container_width=True):
            if username == "admin@company.com" and password and two_factor:
                st.session_state.admin_authenticated = True
                st.session_state.admin_username = "System Administrator"
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error("Invalid credentials or 2FA code")

def show_system_overview():
    """Display system overview"""
    st.markdown("### 📊 System Overview")
    
    # System status
    system_status = api_client.get_system_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_class = "status-healthy" if system_status["status"] == "healthy" else "status-error"
        st.markdown(f"""
        <div class="system-metric">
            <h3>🟢 System Status</h3>
            <p class="{status_class}">{system_status["status"].upper()}</p>
            <small>Uptime: {system_status["uptime"]}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="system-metric">
            <h3>📈 Version</h3>
            <p><strong>{system_status["version"]}</strong></p>
            <small>Last deploy: Today</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        metrics = api_client.get_system_metrics()
        st.markdown(f"""
        <div class="system-metric">
            <h3>📋 Applications</h3>
            <p><strong>{metrics["applications"]["today"]}</strong></p>
            <small>Today / {metrics["applications"]["total"]} total</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:  
        st.markdown(f"""
        <div class="system-metric">
            <h3>⚡ Performance</h3>
            <p><strong>{metrics["performance"]["success_rate"]}</strong></p>
            <small>Success rate</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Services status
    st.markdown("#### 🔧 Service Status")
    
    services = system_status["services"]
    service_cols = st.columns(len(services))
    
    for i, (service_name, service_data) in enumerate(services.items()):
        with service_cols[i]:
            status_icon = "🟢" if service_data["status"] == "healthy" else "🔴"
            st.markdown(f"""
            <div class="admin-card">
                <h4>{status_icon} {service_name.replace('_', ' ').title()}</h4>
                <p><strong>Status:</strong> {service_data["status"]}</p>
                {f"<p><strong>Response:</strong> {service_data.get('response_time', 'N/A')}</p>" if 'response_time' in service_data else ""}
                {f"<p><strong>Connections:</strong> {service_data.get('connections', 'N/A')}</p>" if 'connections' in service_data else ""}
                {f"<p><strong>Usage:</strong> {service_data.get('usage', service_data.get('quota_used', 'N/A'))}</p>" if 'usage' in service_data or 'quota_used' in service_data else ""}
            </div>
            """, unsafe_allow_html=True)

def show_user_management():
    """Display user management interface"""
    st.markdown("### 👥 User Management")
    
    # User statistics
    users_data = api_client.get_user_management_data()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = len(users_data)
        st.metric("Total Users", total_users)
    
    with col2:
        active_users = len([u for u in users_data if u["status"] == "active"])
        st.metric("Active Users", active_users)
    
    with col3:
        admin_users = len([u for u in users_data if "admin" in u["role"]])
        st.metric("Admin Users", admin_users)
    
    with col4:
        analysts = len([u for u in users_data if "analyst" in u["role"]])
        st.metric("Analysts", analysts)
    
    # User list and management
    st.markdown("#### 👤 User Accounts")
    
    # Add user form
    with st.expander("➕ Add New User"):
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username/Email")
                new_role = st.selectbox("Role", ["admin", "senior_analyst", "analyst", "viewer"])
            
            with col2:
                new_password = st.text_input("Temporary Password", type="password")
                send_invite = st.checkbox("Send invitation email")
            
            if st.form_submit_button("Create User"):
                st.success(f"✅ User {new_username} created successfully!")
    
    # User list
    for user in users_data:
        status_color = "#4caf50" if user["status"] == "active" else "#f44336"
        
        st.markdown(f"""
        <div class="user-row">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0;">{user["username"]}</h4>
                    <p style="margin: 0.2rem 0;">
                        <strong>Role:</strong> {user["role"].replace('_', ' ').title()} | 
                        <strong>Status:</strong> <span style="color: {status_color};">{user["status"].upper()}</span>
                    </p>
                    <small>Last login: {user["last_login"][:16]} | Created: {user["created_at"][:10]}</small>
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <button style="background: #2196f3; color: white; border: none; padding: 0.3rem 0.8rem; border-radius: 4px;">Edit</button>
                    <button style="background: #ff9800; color: white; border: none; padding: 0.3rem 0.8rem; border-radius: 4px;">Reset</button>
                    <button style="background: #f44336; color: white; border: none; padding: 0.3rem 0.8rem; border-radius: 4px;">Disable</button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_system_configuration():
    """Display system configuration interface"""
    st.markdown("### ⚙️ System Configuration")
    
    # Configuration sections
    config_tabs = st.tabs(["🔧 General", "🔒 Security", "🤖 AI Services", "📊 Workflows", "💾 Storage"])
    
    with config_tabs[0]:  # General
        st.markdown("#### General Settings")
        
        with st.form("general_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                system_name = st.text_input("System Name", value="KYC Document Analyzer")
                max_file_size = st.number_input("Max File Size (MB)", value=10, min_value=1, max_value=100)
                session_timeout = st.number_input("Session Timeout (minutes)", value=30, min_value=5, max_value=480)
            
            with col2:
                default_language = st.selectbox("Default Language", ["English", "Spanish", "French", "German"])
                timezone = st.selectbox("System Timezone", ["UTC", "EST", "PST", "GMT"])
                maintenance_mode = st.checkbox("Maintenance Mode")
            
            if st.form_submit_button("💾 Save General Settings"):
                st.success("✅ General settings saved successfully!")
    
    with config_tabs[1]:  # Security
        st.markdown("#### Security Configuration")
        
        with st.form("security_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                password_policy = st.selectbox("Password Policy", ["Standard", "Strong", "Enterprise"])
                mfa_required = st.checkbox("Require 2FA", value=True)
                session_security = st.selectbox("Session Security", ["Standard", "High", "Maximum"])
            
            with col2:
                login_attempts = st.number_input("Max Login Attempts", value=5, min_value=3, max_value=10)
                lockout_duration = st.number_input("Lockout Duration (minutes)", value=30, min_value=5, max_value=1440)
                audit_retention = st.number_input("Audit Log Retention (days)", value=90, min_value=30, max_value=365)
            
            if st.form_submit_button("🔒 Save Security Settings"):
                st.success("✅ Security settings saved successfully!")
    
    with config_tabs[2]:  # AI Services
        st.markdown("#### AI Services Configuration")
        
        with st.form("ai_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                azure_endpoint = st.text_input("Azure AI Endpoint", value="https://your-resource.cognitiveservices.azure.com/")
                confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.8, 0.1)
                max_retries = st.number_input("Max API Retries", value=3, min_value=1, max_value=10)
            
            with col2:
                api_timeout = st.number_input("API Timeout (seconds)", value=30, min_value=5, max_value=300)
                enable_caching = st.checkbox("Enable Response Caching", value=True)
                cache_ttl = st.number_input("Cache TTL (minutes)", value=60, min_value=5, max_value=1440)
            
            if st.form_submit_button("🤖 Save AI Configuration"):
                st.success("✅ AI services configuration saved!")
    
    with config_tabs[3]:  # Workflows
        st.markdown("#### Workflow Configuration")
        
        with st.form("workflow_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                auto_approval_threshold = st.slider("Auto-approval Risk Threshold", 0.0, 1.0, 0.3, 0.1)
                manual_review_threshold = st.slider("Manual Review Threshold", 0.0, 1.0, 0.7, 0.1)
                priority_processing = st.checkbox("Priority Processing", value=True)
            
            with col2:
                workflow_timeout = st.number_input("Workflow Timeout (hours)", value=72, min_value=1, max_value=168)
                max_concurrent = st.number_input("Max Concurrent Workflows", value=50, min_value=1, max_value=200)
                retry_failed = st.checkbox("Auto-retry Failed Workflows", value=True)
            
            if st.form_submit_button("📊 Save Workflow Settings"):
                st.success("✅ Workflow configuration saved!")
    
    with config_tabs[4]:  # Storage
        st.markdown("#### Storage Configuration")
        
        with st.form("storage_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                retention_period = st.number_input("Document Retention (days)", value=2555, min_value=365, max_value=3650)  # 7 years default
                backup_frequency = st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"])
                compression_enabled = st.checkbox("Enable Compression", value=True)
            
            with col2:
                storage_quota = st.number_input("Storage Quota (GB)", value=500, min_value=100, max_value=10000)
                auto_cleanup = st.checkbox("Auto Cleanup Expired Documents", value=True)
                encryption_enabled = st.checkbox("Enable Encryption at Rest", value=True)
            
            if st.form_submit_button("💾 Save Storage Settings"):
                st.success("✅ Storage configuration saved!")

def show_monitoring_alerts():
    """Display monitoring and alerts"""
    st.markdown("### 🚨 Monitoring & Alerts")
    
    # System alerts
    alerts = api_client.get_system_alerts()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 🔔 Active Alerts")
        
        for alert in alerts:
            if not alert["resolved"]:
                alert_class = f"alert-{alert['severity']}"
                severity_icon = {"high": "🔴", "medium": "🟡", "info": "🔵"}[alert["severity"]]
                
                st.markdown(f"""
                <div class="admin-card {alert_class}">
                    <h4>{severity_icon} {alert["type"].title()} Alert</h4>
                    <p><strong>{alert["message"]}</strong></p>
                    <small>ID: {alert["id"]} | Time: {alert["timestamp"][:16]}</small>
                </div>
                """, unsafe_allow_html=True)
                
                col_resolve, col_snooze = st.columns(2)
                with col_resolve:
                    if st.button(f"✅ Resolve", key=f"resolve_{alert['id']}"):
                        st.success(f"Alert {alert['id']} resolved")
                with col_snooze:
                    if st.button(f"⏰ Snooze", key=f"snooze_{alert['id']}"):
                        st.info(f"Alert {alert['id']} snoozed for 1 hour")
    
    with col2:
        st.markdown("#### 📊 Alert Summary")
        
        alert_summary = {"high": 1, "medium": 1, "info": 1}
        
        for severity, count in alert_summary.items():
            color = {"high": "#f44336", "medium": "#ff9800", "info": "#2196f3"}[severity]
            st.markdown(f"""
            <div class="system-metric" style="border-left-color: {color};">
                <h4>{severity.title()} Priority</h4>
                <p><strong>{count}</strong></p>
                <small>Active alerts</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Performance metrics
    st.markdown("#### 📈 Performance Monitoring")
    
    # Sample performance data
    perf_data = pd.DataFrame({
        'Time': pd.date_range(start='2025-09-17T00:00:00', periods=24, freq='H'),
        'API_Response': [45, 42, 48, 52, 49, 46, 51, 47, 44, 49, 53, 58, 61, 65, 62, 59, 56, 54, 51, 48, 46, 43, 41, 44],
        'CPU_Usage': [25, 23, 28, 32, 29, 26, 31, 27, 24, 29, 33, 38, 41, 45, 42, 39, 36, 34, 31, 28, 26, 23, 21, 24],
        'Memory_Usage': [65, 63, 68, 72, 69, 66, 71, 67, 64, 69, 73, 78, 81, 85, 82, 79, 76, 74, 71, 68, 66, 63, 61, 64]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_response = px.line(perf_data, x='Time', y='API_Response', title='API Response Time (ms)')
        st.plotly_chart(fig_response, use_container_width=True)
    
    with col2:
        fig_resources = px.line(perf_data, x='Time', y=['CPU_Usage', 'Memory_Usage'], 
                               title='System Resource Usage (%)')
        st.plotly_chart(fig_resources, use_container_width=True)

def show_audit_logs():
    """Display audit logs"""
    st.markdown("### 📜 Audit Logs")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        log_level = st.selectbox("Severity", ["All", "info", "warning", "error"])
    with col2:
        event_type = st.selectbox("Event Type", ["All", "user_login", "kyc_workflow", "document_upload", "system"])
    with col3:
        date_from = st.date_input("From Date", value=datetime.now().date() - timedelta(days=7))
    with col4:
        date_to = st.date_input("To Date", value=datetime.now().date())
    
    # Get audit logs
    logs = api_client.get_audit_logs()
    
    # Display logs
    st.markdown("#### 📋 Recent Activity")
    
    for log in logs:
        severity_color = {
            "info": "#2196f3",
            "warning": "#ff9800", 
            "error": "#f44336"
        }.get(log["severity"], "#666")
        
        st.markdown(f"""
        <div class="user-row" style="border-left-color: {severity_color};">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <h4 style="margin: 0; color: {severity_color};">{log["event_type"].replace('_', ' ').title()}</h4>
                    <p style="margin: 0.2rem 0;"><strong>User:</strong> {log["user"]}</p>
                    <p style="margin: 0.2rem 0;">{log["details"]}</p>
                </div>
                <div style="text-align: right;">
                    <small>{log["timestamp"][:16]}</small><br>
                    <span style="color: {severity_color}; font-weight: bold;">{log["severity"].upper()}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Export logs
    if st.button("📥 Export Logs", use_container_width=False):
        logs_df = pd.DataFrame(logs)
        csv = logs_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def show_sidebar():
    """Display admin sidebar"""
    with st.sidebar:
        st.markdown("### ⚙️ Admin Tools")
        
        if st.session_state.admin_authenticated:
            st.markdown(f"**{st.session_state.admin_username}**")
            st.markdown("---")
            
            # System status summary
            st.markdown("#### System Status")
            st.markdown("🟢 **All Systems Operational**")
            st.markdown("• API: Healthy")
            st.markdown("• Database: Healthy") 
            st.markdown("• Storage: 47% Used")
            
            st.markdown("---")
            
            # Quick actions
            st.markdown("#### Quick Actions")
            
            if st.button("🔄 System Restart", use_container_width=True):
                st.warning("⚠️ System restart initiated")
            
            if st.button("💾 Create Backup", use_container_width=True):
                st.success("✅ Backup created successfully")
            
            if st.button("🧹 Clear Cache", use_container_width=True):
                st.info("🗑️ System cache cleared")
            
            if st.button("📊 Health Check", use_container_width=True):
                st.success("✅ All systems healthy")
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if 'admin' in key:
                        del st.session_state[key]
                st.rerun()

def main():
    """Main application entry point"""
    init_session_state()
    show_header()
    show_sidebar()
    
    if not st.session_state.admin_authenticated:
        show_login()
        return
    
    # Main admin tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "👥 Users", 
        "⚙️ Configuration", 
        "🚨 Monitoring", 
        "📜 Audit Logs"
    ])
    
    with tab1:
        show_system_overview()
    
    with tab2:
        show_user_management()
    
    with tab3:
        show_system_configuration()
    
    with tab4:
        show_monitoring_alerts()
    
    with tab5:
        show_audit_logs()

if __name__ == "__main__":
    main()
