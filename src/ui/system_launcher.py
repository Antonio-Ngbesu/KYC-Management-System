"""
KYC System UI Launcher
Unified launcher for all user interfaces with role-based access
"""
import streamlit as st
import subprocess
import sys
import os
from pathlib import Path
import time
import requests
from typing import Dict, Any, Optional
import json

# Configure Streamlit
st.set_page_config(
    page_title="KYC System Hub",
    page_icon="🏦",
    layout="wide"
)

# Custom CSS for modern launcher
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global app styling */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
    
    /* Main title styling */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .main-title::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: shine 4s ease-in-out infinite;
    }
    
    @keyframes shine {
        0%, 100% { opacity: 0.3; transform: rotate(0deg); }
        50% { opacity: 0.6; transform: rotate(180deg); }
    }
    
    .main-title h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 3rem;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        position: relative;
        z-index: 1;
    }
    
    .main-title p {
        font-family: 'Inter', sans-serif;
        font-size: 1.3rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
    }
    
    .main-title small {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        opacity: 0.8;
        position: relative;
        z-index: 1;
    }
    
    /* Interface cards */
    .interface-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border: 2px solid #e1e8ed;
        border-radius: 20px;
        padding: 2.5rem;
        margin: 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        cursor: pointer;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .interface-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .interface-card:hover::before {
        transform: scaleX(1);
    }
    
    .interface-card:hover {
        border-color: #667eea;
        box-shadow: 0 20px 40px rgba(102,126,234,0.25);
        transform: translateY(-10px) scale(1.02);
    }
    
    .interface-card.customer {
        border-left: 6px solid #28a745;
    }
    
    .interface-card.customer:hover {
        box-shadow: 0 20px 40px rgba(40, 167, 69, 0.3);
    }
    
    .interface-card.analyst {
        border-left: 6px solid #007bff;
    }
    
    .interface-card.analyst:hover {
        box-shadow: 0 20px 40px rgba(0, 123, 255, 0.3);
    }
    
    .interface-card.admin {
        border-left: 6px solid #6f42c1;
    }
    
    .interface-card.admin:hover {
        box-shadow: 0 20px 40px rgba(111, 66, 193, 0.3);
    }
    
    .interface-card h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.5rem;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .interface-card p {
        font-family: 'Inter', sans-serif;
        color: #6c757d;
        margin-bottom: 1rem;
    }
    
    .interface-card ul {
        text-align: left;
        font-family: 'Inter', sans-serif;
        color: #495057;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse-dot 2s infinite;
    }
    
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .status-running { 
        background-color: #28a745;
        box-shadow: 0 0 10px rgba(40, 167, 69, 0.5);
    }
    
    .status-stopped { 
        background-color: #dc3545;
        box-shadow: 0 0 10px rgba(220, 53, 69, 0.5);
    }
    
    .status-loading { 
        background-color: #ffc107;
        box-shadow: 0 0 10px rgba(255, 193, 7, 0.5);
    }
    
    /* System stats cards */
    .system-stats {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid #e1e8ed;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .system-stats:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.15);
    }
    
    .system-stats h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .system-stats p {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    
    .system-stats small {
        font-family: 'Inter', sans-serif;
        color: #6c757d;
    }
    
    /* Quick actions */
    .quick-actions {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid #bbdefb;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }
    
    .quick-actions h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #1565c0;
        margin-bottom: 1rem;
    }
    
    .quick-actions ul {
        font-family: 'Inter', sans-serif;
        color: #1976d2;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Metrics */
    .css-1xarl3l {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e1e8ed;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        border-radius: 15px;
        padding: 1rem 2rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        border: 2px solid #e1e8ed;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #667eea;
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    }
</style>
""", unsafe_allow_html=True)

# Configuration
BASE_DIR = Path(__file__).parent.parent
API_BASE_URL = "http://localhost:8000"
UI_PORTS = {
    "customer": 8501,
    "analyst": 8502,
    "admin": 8503
}

class SystemManager:
    """Manages the KYC system components"""
    
    def __init__(self):
        self.processes = {}
        self.api_running = False
    
    def check_api_status(self) -> bool:
        """Check if the main API is running"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_api_server(self):
        """Start the main FastAPI server"""
        if not self.check_api_status():
            try:
                # Start FastAPI server
                cmd = [
                    sys.executable, "-m", "uvicorn",
                    "src.api.main:app",
                    "--host", "0.0.0.0",
                    "--port", "8000",
                    "--reload"
                ]
                
                process = subprocess.Popen(
                    cmd,
                    cwd=BASE_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.processes["api"] = process
                return True
            except Exception as e:
                st.error(f"Failed to start API server: {e}")
                return False
        return True
    
    def start_ui_interface(self, interface_type: str) -> bool:
        """Start a Streamlit UI interface"""
        try:
            port = UI_PORTS[interface_type]
            ui_file = f"src/ui/{interface_type}_portal.py" if interface_type == "customer" else f"src/ui/{interface_type}_dashboard.py"
            
            # Check if interface is already running
            if self.check_port_in_use(port):
                return True
            
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                ui_file,
                "--server.port", str(port),
                "--server.headless", "true"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes[interface_type] = process
            return True
            
        except Exception as e:
            st.error(f"Failed to start {interface_type} interface: {e}")
            return False
    
    def stop_interface(self, interface_type: str):
        """Stop a running interface"""
        if interface_type in self.processes:
            try:
                self.processes[interface_type].terminate()
                del self.processes[interface_type]
            except:
                pass
    
    def check_port_in_use(self, port: int) -> bool:
        """Check if a port is in use"""
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            return True
        except:
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "api": self.check_api_status(),
            "customer_portal": self.check_port_in_use(UI_PORTS["customer"]),
            "analyst_dashboard": self.check_port_in_use(UI_PORTS["analyst"]),
            "admin_dashboard": self.check_port_in_use(UI_PORTS["admin"])
        }

# Initialize system manager
if 'system_manager' not in st.session_state:
    st.session_state.system_manager = SystemManager()

def show_header():
    """Display main header"""
    st.markdown("""
    <div class="main-title">
        <h1>🏦 KYC Document Analyzer System</h1>
        <p>Professional Identity Verification & Compliance Platform</p>
        <small>Production-Ready Banking Solution</small>
    </div>
    """, unsafe_allow_html=True)

def show_system_status():
    """Display system status overview"""
    status = st.session_state.system_manager.get_system_status()
    
    st.markdown("### 📊 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        api_status = "🟢 Running" if status["api"] else "🔴 Stopped"
        st.markdown(f"""
        <div class="system-stats">
            <h4>🔧 API Server</h4>
            <p>{api_status}</p>
            <small>Port: 8000</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        customer_status = "🟢 Running" if status["customer_portal"] else "🔴 Stopped"
        st.markdown(f"""
        <div class="system-stats">
            <h4>👤 Customer Portal</h4>
            <p>{customer_status}</p>
            <small>Port: {UI_PORTS["customer"]}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        analyst_status = "🟢 Running" if status["analyst_dashboard"] else "🔴 Stopped"
        st.markdown(f"""
        <div class="system-stats">
            <h4>🔍 Analyst Dashboard</h4>
            <p>{analyst_status}</p>
            <small>Port: {UI_PORTS["analyst"]}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        admin_status = "🟢 Running" if status["admin_dashboard"] else "🔴 Stopped"
        st.markdown(f"""
        <div class="system-stats">
            <h4>⚙️ Admin Dashboard</h4>
            <p>{admin_status}</p>
            <small>Port: {UI_PORTS["admin"]}</small>
        </div>
        """, unsafe_allow_html=True)

def show_interface_cards():
    """Display interface launch cards"""
    st.markdown("### 🚀 Launch Interfaces")
    
    status = st.session_state.system_manager.get_system_status()
    
    col1, col2, col3 = st.columns(3)
    
    # Customer Portal
    with col1:
        st.markdown("""
        <div class="interface-card customer">
            <h3>👤 Customer Portal</h3>
            <p><strong>For End Users</strong></p>
            <ul style="text-align: left;">
                <li>Document Upload</li>
                <li>KYC Status Tracking</li>
                <li>Real-time Notifications</li>
                <li>Profile Management</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if status["customer_portal"]:
            if st.button("🌐 Open Customer Portal", key="customer_open", use_container_width=True):
                st.success("Opening Customer Portal...")
                st.markdown(f"**[Click here to access Customer Portal](http://localhost:{UI_PORTS['customer']})**")
        else:
            if st.button("🚀 Launch Customer Portal", key="customer_launch", use_container_width=True):
                with st.spinner("Starting Customer Portal..."):
                    if st.session_state.system_manager.start_ui_interface("customer"):
                        time.sleep(3)  # Wait for startup
                        st.success("Customer Portal started!")
                        st.rerun()
                    else:
                        st.error("Failed to start Customer Portal")
    
    # Analyst Dashboard
    with col2:
        st.markdown("""
        <div class="interface-card analyst">
            <h3>🔍 Analyst Dashboard</h3>
            <p><strong>For KYC Analysts</strong></p>
            <ul style="text-align: left;">
                <li>Review Queue</li>
                <li>Risk Assessment</li>
                <li>Decision Tools</li>
                <li>Analytics & Reports</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if status["analyst_dashboard"]:
            if st.button("🌐 Open Analyst Dashboard", key="analyst_open", use_container_width=True):
                st.success("Opening Analyst Dashboard...")
                st.markdown(f"**[Click here to access Analyst Dashboard](http://localhost:{UI_PORTS['analyst']})**")
        else:
            if st.button("🚀 Launch Analyst Dashboard", key="analyst_launch", use_container_width=True):
                with st.spinner("Starting Analyst Dashboard..."):
                    if st.session_state.system_manager.start_ui_interface("analyst"):
                        time.sleep(3)  # Wait for startup
                        st.success("Analyst Dashboard started!")
                        st.rerun()
                    else:
                        st.error("Failed to start Analyst Dashboard")
    
    # Admin Dashboard
    with col3:
        st.markdown("""
        <div class="interface-card admin">
            <h3>⚙️ Admin Dashboard</h3>
            <p><strong>For System Administrators</strong></p>
            <ul style="text-align: left;">
                <li>System Management</li>
                <li>User Administration</li>
                <li>Configuration</li>
                <li>Monitoring & Alerts</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if status["admin_dashboard"]:
            if st.button("🌐 Open Admin Dashboard", key="admin_open", use_container_width=True):
                st.success("Opening Admin Dashboard...")
                st.markdown(f"**[Click here to access Admin Dashboard](http://localhost:{UI_PORTS['admin']})**")
        else:
            if st.button("🚀 Launch Admin Dashboard", key="admin_launch", use_container_width=True):
                with st.spinner("Starting Admin Dashboard..."):
                    if st.session_state.system_manager.start_ui_interface("admin"):
                        time.sleep(3)  # Wait for startup
                        st.success("Admin Dashboard started!")
                        st.rerun()
                    else:
                        st.error("Failed to start Admin Dashboard")

def show_quick_actions():
    """Display quick action buttons"""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔧 Start API Server", use_container_width=True):
            with st.spinner("Starting API server..."):
                if st.session_state.system_manager.start_api_server():
                    time.sleep(5)  # Wait for startup
                    st.success("API server started!")
                    st.rerun()
                else:
                    st.error("Failed to start API server")
    
    with col2:
        if st.button("🚀 Launch All Interfaces", use_container_width=True):
            with st.spinner("Starting all interfaces..."):
                # Start API first
                st.session_state.system_manager.start_api_server()
                time.sleep(3)
                
                # Start all UI interfaces
                for interface in ["customer", "analyst", "admin"]:
                    st.session_state.system_manager.start_ui_interface(interface)
                    time.sleep(2)
                
                st.success("All interfaces started!")
                st.rerun()
    
    with col3:
        if st.button("📊 System Health Check", use_container_width=True):
            with st.spinner("Checking system health..."):
                status = st.session_state.system_manager.get_system_status()
                running_services = sum(1 for s in status.values() if s)
                total_services = len(status)
                
                if running_services == total_services:
                    st.success(f"✅ All {total_services} services are running!")
                else:
                    st.warning(f"⚠️ {running_services}/{total_services} services running")
    
    with col4:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()

def show_system_info():
    """Display system information"""
    st.markdown("### 📋 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="quick-actions">
            <h4>🏗️ Architecture</h4>
            <ul>
                <li><strong>Backend:</strong> FastAPI + PostgreSQL</li>
                <li><strong>Frontend:</strong> Streamlit Multi-App</li>
                <li><strong>AI Services:</strong> Azure Cognitive Services</li>
                <li><strong>Storage:</strong> Azure Blob Storage</li>
                <li><strong>Notifications:</strong> WebSocket Real-time</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="quick-actions">
            <h4>🔗 Service URLs</h4>
            <ul>
                <li><strong>API:</strong> http://localhost:8000</li>
                <li><strong>Customer Portal:</strong> http://localhost:8501</li>
                <li><strong>Analyst Dashboard:</strong> http://localhost:8502</li>
                <li><strong>Admin Dashboard:</strong> http://localhost:8503</li>
                <li><strong>API Docs:</strong> http://localhost:8000/docs</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_features_overview():
    """Display features overview"""
    st.markdown("### ✨ Key Features")
    
    features = [
        {
            "category": "🔒 Security & Compliance",
            "items": [
                "Bank-grade security controls",
                "Comprehensive audit logging",
                "Role-based access control",
                "PII detection and redaction",
                "Document retention policies"
            ]
        },
        {
            "category": "🤖 AI-Powered Processing",
            "items": [
                "Automated document analysis",
                "Identity verification",
                "Risk assessment algorithms",
                "Authenticity checking",
                "Intelligent workflow routing"
            ]
        },
        {
            "category": "📊 Management & Analytics",
            "items": [
                "Real-time dashboards",
                "Performance metrics",
                "Risk analytics",
                "User management",
                "System monitoring"
            ]
        },
        {
            "category": "🔄 Workflow Automation",
            "items": [
                "Automated KYC processing",
                "Smart decision-making",
                "Exception handling",
                "Manual review queue",
                "Status notifications"
            ]
        }
    ]
    
    cols = st.columns(2)
    
    for i, feature in enumerate(features):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="system-stats">
                <h4>{feature['category']}</h4>
                <ul>
                    {''.join(f'<li>{item}</li>' for item in feature['items'])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main application entry point"""
    show_header()
    
    # Auto-refresh every 30 seconds to update status
    if st.button("🔄 Auto-refresh (30s)", help="Page will refresh automatically"):
        time.sleep(30)
        st.rerun()
    
    show_system_status()
    
    st.markdown("---")
    
    show_interface_cards()
    
    st.markdown("---")
    
    show_quick_actions()
    
    st.markdown("---")
    
    # Tabs for additional information
    tab1, tab2 = st.tabs(["📋 System Info", "✨ Features"])
    
    with tab1:
        show_system_info()
    
    with tab2:
        show_features_overview()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🏦 KYC Document Analyzer v2.0.0 | Production-Ready Banking Solution</p>
        <p>Built with FastAPI, Streamlit, Azure AI Services, and PostgreSQL</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
