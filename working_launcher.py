"""
KYC System Launcher - Fixed Version
Clean, functional launcher without CSS conflicts
"""
import streamlit as st
import subprocess
import sys
import requests
import time
from pathlib import Path

# Basic Streamlit configuration
st.set_page_config(
    page_title="KYC System Hub",
    page_icon="🏦",
    layout="wide"
)

# Minimal CSS that won't interfere with functionality
st.markdown("""
<style>
    .main-title {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .service-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .status-running { color: #28a745; font-weight: bold; }
    .status-stopped { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Configuration
UI_PORTS = {
    "customer": 8501,
    "analyst": 8502,
    "admin": 8503
}

def check_service_status(port):
    """Check if a service is running on specified port"""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_api_status():
    """Check if API is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# Header
st.markdown("""
<div class="main-title">
    <h1>🏦 KYC Document Analyzer System</h1>
    <p>Professional Identity Verification & Compliance Platform</p>
</div>
""", unsafe_allow_html=True)

# System status overview
st.markdown("## 📊 System Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    api_running = check_api_status()
    status_text = "🟢 Running" if api_running else "🔴 Stopped"
    st.metric("API Server", status_text)

with col2:
    customer_running = check_service_status(8501)
    status_text = "🟢 Running" if customer_running else "🔴 Stopped"
    st.metric("Customer Portal", status_text)

with col3:
    analyst_running = check_service_status(8502)
    status_text = "🟢 Running" if analyst_running else "🔴 Stopped"
    st.metric("Analyst Dashboard", status_text)

with col4:
    admin_running = check_service_status(8503)
    status_text = "🟢 Running" if admin_running else "🔴 Stopped"
    st.metric("Admin Dashboard", status_text)

st.markdown("---")

# Service launcher section
st.markdown("## 🚀 Launch Services")

# Row 1: Customer and Analyst
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="service-card">
        <h3>👤 Customer Portal</h3>
        <p><strong>For End Users</strong></p>
        <ul>
            <li>Document Upload</li>
            <li>KYC Status Tracking</li>
            <li>Real-time Notifications</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if customer_running:
        if st.button("🌐 Open Customer Portal", key="customer_open", use_container_width=True):
            st.success("Opening Customer Portal...")
            st.markdown("[**Click here to access Customer Portal →**](http://localhost:8501)")
    else:
        if st.button("🚀 Start Customer Portal", key="customer_start", use_container_width=True):
            st.info("Starting Customer Portal...")
            st.markdown("**Command to run manually:**")
            st.code("streamlit run src/ui/customer_portal.py --server.port 8501")

with col2:
    st.markdown("""
    <div class="service-card">
        <h3>🔍 Analyst Dashboard</h3>
        <p><strong>For KYC Analysts</strong></p>
        <ul>
            <li>Review Queue</li>
            <li>Risk Assessment</li>
            <li>Decision Tools</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if analyst_running:
        if st.button("🌐 Open Analyst Dashboard", key="analyst_open", use_container_width=True):
            st.success("Opening Analyst Dashboard...")
            st.markdown("[**Click here to access Analyst Dashboard →**](http://localhost:8502)")
    else:
        if st.button("🚀 Start Analyst Dashboard", key="analyst_start", use_container_width=True):
            st.info("Starting Analyst Dashboard...")
            st.markdown("**Command to run manually:**")
            st.code("streamlit run src/ui/analyst_dashboard.py --server.port 8502")

# Row 2: Admin and API
col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    <div class="service-card">
        <h3>⚙️ Admin Dashboard</h3>
        <p><strong>For System Administrators</strong></p>
        <ul>
            <li>System Management</li>
            <li>User Administration</li>
            <li>Configuration</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if admin_running:
        if st.button("🌐 Open Admin Dashboard", key="admin_open", use_container_width=True):
            st.success("Opening Admin Dashboard...")
            st.markdown("[**Click here to access Admin Dashboard →**](http://localhost:8503)")
    else:
        if st.button("🚀 Start Admin Dashboard", key="admin_start", use_container_width=True):
            st.info("Starting Admin Dashboard...")
            st.markdown("**Command to run manually:**")
            st.code("streamlit run src/ui/admin_dashboard.py --server.port 8503")

with col4:
    st.markdown("""
    <div class="service-card">
        <h3>🔧 API Server</h3>
        <p><strong>Backend Services</strong></p>
        <ul>
            <li>REST API</li>
            <li>Document Processing</li>
            <li>Database Operations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if api_running:
        if st.button("📚 Open API Documentation", key="api_docs", use_container_width=True):
            st.success("Opening API Documentation...")
            st.markdown("[**Click here to access API Docs →**](http://localhost:8000/docs)")
    else:
        if st.button("🚀 Start API Server", key="api_start", use_container_width=True):
            st.info("Starting API Server...")
            st.markdown("**Command to run manually:**")
            st.code("uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload")

st.markdown("---")

# Quick actions
st.markdown("## ⚡ Quick Actions")

action_col1, action_col2, action_col3 = st.columns(3)

with action_col1:
    if st.button("🚀 Start All Services", use_container_width=True):
        st.info("Use the automated startup script:")
        st.code("python start_system.py start")

with action_col2:
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.rerun()

with action_col3:
    if st.button("🔧 System Health Check", use_container_width=True):
        st.info("Checking all services...")
        services_status = {
            "API Server": check_api_status(),
            "Customer Portal": check_service_status(8501),
            "Analyst Dashboard": check_service_status(8502),
            "Admin Dashboard": check_service_status(8503)
        }
        
        running_count = sum(services_status.values())
        total_count = len(services_status)
        
        if running_count == total_count:
            st.success(f"✅ All {total_count} services are running!")
        else:
            st.warning(f"⚠️ {running_count}/{total_count} services running")
            
        for service, status in services_status.items():
            status_icon = "✅" if status else "❌"
            st.write(f"{status_icon} {service}")

st.markdown("---")

# Manual commands section
st.markdown("## 📋 Manual Commands")

st.markdown("**If buttons don't work, use these commands in your terminal:**")

commands = {
    "Start API Server": "uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload",
    "Start Customer Portal": "streamlit run src/ui/customer_portal.py --server.port 8501",
    "Start Analyst Dashboard": "streamlit run src/ui/analyst_dashboard.py --server.port 8502",
    "Start Admin Dashboard": "streamlit run src/ui/admin_dashboard.py --server.port 8503",
    "Start All Services": "python start_system.py start"
}

for service, command in commands.items():
    with st.expander(f"📝 {service}"):
        st.code(command)
        st.write("Copy and paste this command into your terminal/command prompt")

# Service URLs
st.markdown("## 🌐 Service URLs")

urls = {
    "System Launcher": "http://localhost:8512 (this page)",
    "Customer Portal": "http://localhost:8501",
    "Analyst Dashboard": "http://localhost:8502",
    "Admin Dashboard": "http://localhost:8503",
    "API Server": "http://localhost:8000",
    "API Documentation": "http://localhost:8000/docs"
}

for service, url in urls.items():
    st.write(f"**{service}:** {url}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🏦 KYC Document Analyzer System v2.0.0</p>
    <p>Built with FastAPI, Streamlit, Azure AI Services, and PostgreSQL</p>
</div>
""", unsafe_allow_html=True)
