"""
KYC System Launcher - Authentication Enabled
Secure launcher with development authentication
"""
import streamlit as st
import subprocess
import sys
import os
import requests
import time
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.auth.dev_auth import show_login_form, show_user_info, dev_auth, require_auth
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

# Basic Streamlit configuration
st.set_page_config(
    page_title="KYC System Hub",
    page_icon="🏦",
    layout="wide"
)

# Simple CSS that won't interfere with functionality
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
    .auth-info {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
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
        return True
    except:
        return False

def check_api_status():
    """Check if the API is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def launch_service(script_path, description, port=None):
    """Launch a service in a new terminal window"""
    try:
        if os.name == 'nt':  # Windows
            if port:
                cmd = f'streamlit run "{script_path}" --server.port {port}'
            else:
                cmd = f'streamlit run "{script_path}"'
            subprocess.Popen(['start', 'cmd', '/k', cmd], shell=True)
        else:  # Unix/Linux/Mac
            if port:
                subprocess.Popen(['gnome-terminal', '--', 'streamlit', 'run', script_path, '--server.port', str(port)])
            else:
                subprocess.Popen(['gnome-terminal', '--', 'streamlit', 'run', script_path])
        return True
    except Exception as e:
        st.error(f"Failed to launch {description}: {str(e)}")
        return False

def launch_api():
    """Launch the API server"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(['start', 'cmd', '/k', 'cd src && python -m uvicorn api.main:app --reload --port 8000'], shell=True)
        else:
            subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 'cd src && python -m uvicorn api.main:app --reload --port 8000'])
        return True
    except Exception as e:
        st.error(f"Failed to launch API: {str(e)}")
        return False

def main():
    # Show header
    st.markdown("""
    <div class="main-title">
        <h1>🏦 KYC System Control Hub</h1>
        <p>Secure Know Your Customer Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication section
    if AUTH_AVAILABLE:
        if not dev_auth.is_authenticated():
            st.markdown("### 🔐 Authentication Required")
            st.markdown("""
            <div class="auth-info">
                <strong>Please login to access the KYC system</strong><br>
                Use the demo credentials provided in the login form below.
            </div>
            """, unsafe_allow_html=True)
            
            show_login_form()
            st.stop()
        else:
            # Show user info and logout
            show_user_info()
            user = dev_auth.get_current_user()
    else:
        st.warning("🔓 Running in open mode - Authentication disabled")
        user = {"role": "admin", "name": "Anonymous"}
    
    st.markdown("---")
    
    # System Status
    st.markdown("### 📊 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        api_status = check_api_status()
        status_text = "🟢 Running" if api_status else "🔴 Stopped"
        st.metric("API Server", status_text)
    
    with col2:
        customer_status = check_service_status(UI_PORTS["customer"])
        status_text = "🟢 Running" if customer_status else "🔴 Stopped"
        st.metric("Customer Portal", status_text)
    
    with col3:
        analyst_status = check_service_status(UI_PORTS["analyst"])
        status_text = "🟢 Running" if analyst_status else "🔴 Stopped"
        st.metric("Analyst Dashboard", status_text)
    
    with col4:
        admin_status = check_service_status(UI_PORTS["admin"])
        status_text = "🟢 Running" if admin_status else "🔴 Stopped"
        st.metric("Admin Dashboard", status_text)
    
    st.markdown("---")
    
    # Service Management
    st.markdown("### 🚀 Service Management")
    
    # API Server
    st.markdown("""
    <div class="service-card">
        <h4>🔧 API Server</h4>
        <p>Core backend services and authentication</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🚀 Start API", key="start_api"):
            if launch_api():
                st.success("API server starting...")
                time.sleep(2)
                st.rerun()
    
    with col2:
        if api_status:
            st.success("✅ API server is running on http://localhost:8000")
            if st.button("📖 View API Docs", key="api_docs"):
                st.markdown("[Open API Documentation](http://localhost:8000/docs)")
        else:
            st.warning("⚠️ API server is not running")
    
    # UI Services based on user role
    st.markdown("### 🖥️ User Interfaces")
    
    # Customer Portal
    if user["role"] in ["customer", "analyst", "admin"]:
        st.markdown("""
        <div class="service-card">
            <h4>🏪 Customer Portal</h4>
            <p>Document upload and KYC status tracking</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🚀 Launch", key="launch_customer"):
                script_path = "src/ui/customer_portal.py"
                if Path(script_path).exists():
                    if launch_service(script_path, "Customer Portal", UI_PORTS["customer"]):
                        st.success("Customer Portal starting...")
                else:
                    st.error(f"Script not found: {script_path}")
        
        with col2:
            if customer_status:
                st.success("✅ Running on http://localhost:8501")
            else:
                st.info("💡 Click Launch to start the Customer Portal")
    
    # Analyst Dashboard
    if user["role"] in ["analyst", "admin"]:
        st.markdown("""
        <div class="service-card">
            <h4>🔍 Analyst Dashboard</h4>
            <p>Document review and KYC decision making</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🚀 Launch", key="launch_analyst"):
                script_path = "src/ui/analyst_dashboard.py"
                if Path(script_path).exists():
                    if launch_service(script_path, "Analyst Dashboard", UI_PORTS["analyst"]):
                        st.success("Analyst Dashboard starting...")
                else:
                    st.error(f"Script not found: {script_path}")
        
        with col2:
            if analyst_status:
                st.success("✅ Running on http://localhost:8502")
            else:
                st.info("💡 Click Launch to start the Analyst Dashboard")
    
    # Admin Dashboard
    if user["role"] == "admin":
        st.markdown("""
        <div class="service-card">
            <h4>⚙️ Admin Dashboard</h4>
            <p>System administration and user management</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🚀 Launch", key="launch_admin"):
                script_path = "src/ui/admin_dashboard.py"
                if Path(script_path).exists():
                    if launch_service(script_path, "Admin Dashboard", UI_PORTS["admin"]):
                        st.success("Admin Dashboard starting...")
                else:
                    st.error(f"Script not found: {script_path}")
        
        with col2:
            if admin_status:
                st.success("✅ Running on http://localhost:8503")
            else:
                st.info("💡 Click Launch to start the Admin Dashboard")
    
    # Quick Access Links
    st.markdown("---")
    st.markdown("### 🔗 Quick Access")
    
    if user["role"] in ["customer", "analyst", "admin"] and customer_status:
        st.markdown("- [🏪 Customer Portal](http://localhost:8501)")
    
    if user["role"] in ["analyst", "admin"] and analyst_status:
        st.markdown("- [🔍 Analyst Dashboard](http://localhost:8502)")
    
    if user["role"] == "admin" and admin_status:
        st.markdown("- [⚙️ Admin Dashboard](http://localhost:8503)")
    
    if api_status:
        st.markdown("- [📖 API Documentation](http://localhost:8000/docs)")
    
    # Manual Commands
    with st.expander("💻 Manual Commands"):
        st.markdown("""
        **Start Services Manually:**
        ```bash
        # API Server
        cd src && python -m uvicorn api.main:app --reload --port 8000
        
        # Customer Portal
        streamlit run src/ui/customer_portal.py --server.port 8501
        
        # Analyst Dashboard  
        streamlit run src/ui/analyst_dashboard.py --server.port 8502
        
        # Admin Dashboard
        streamlit run src/ui/admin_dashboard.py --server.port 8503
        ```
        """)
    
    # Refresh and Footer
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**System Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        if st.button("🔄 Refresh Status"):
            st.rerun()

if __name__ == "__main__":
    main()
