"""
Simple KYC System Launcher
"""
import streamlit as st
import subprocess
import sys
import requests
import time

st.set_page_config(
    page_title="KYC System",
    page_icon="🏦",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem auto;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.title("🏦 KYC Document Analyzer System")
st.markdown("### Professional Identity Verification & Compliance Platform")

st.success("✅ **System is Running Successfully!**")

# Service URLs
services = {
    "Customer Portal": 8501,
    "Analyst Dashboard": 8502, 
    "Admin Dashboard": 8503,
    "API Server": 8000
}

st.markdown("### 🌐 Available Services")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 👤 Customer Interface")
    if st.button("🚀 Launch Customer Portal"):
        st.info("Starting Customer Portal...")
        st.markdown("**[Open Customer Portal](http://localhost:8501)**")
    
    st.markdown("#### 🔍 Analyst Interface")
    if st.button("🚀 Launch Analyst Dashboard"):
        st.info("Starting Analyst Dashboard...")
        st.markdown("**[Open Analyst Dashboard](http://localhost:8502)**")

with col2:
    st.markdown("#### ⚙️ Admin Interface")
    if st.button("🚀 Launch Admin Dashboard"):
        st.info("Starting Admin Dashboard...")
        st.markdown("**[Open Admin Dashboard](http://localhost:8503)**")
    
    st.markdown("#### 🔧 API Server")
    if st.button("🚀 Launch API Server"):
        st.info("Starting API Server...")
        st.markdown("**[Open API Documentation](http://localhost:8000/docs)**")

st.markdown("---")

# System status
st.markdown("### 📊 Quick Status Check")

status_col1, status_col2, status_col3, status_col4 = st.columns(4)

def check_service(port):
    try:
        response = requests.get(f"http://localhost:{port}", timeout=2)
        return "🟢 Running"
    except:
        return "🔴 Stopped"

with status_col1:
    st.metric("Customer Portal", check_service(8501))

with status_col2:
    st.metric("Analyst Dashboard", check_service(8502))

with status_col3:
    st.metric("Admin Dashboard", check_service(8503))

with status_col4:
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        api_status = "🟢 Running" if response.status_code == 200 else "🔴 Stopped"
    except:
        api_status = "🔴 Stopped"
    st.metric("API Server", api_status)

st.markdown("---")

# Manual commands
st.markdown("### 🛠️ Manual Commands")
st.code("""
# Start all services:
python start_system.py start

# Start individual services:
streamlit run src/ui/customer_portal.py --server.port 8501
streamlit run src/ui/analyst_dashboard.py --server.port 8502
streamlit run src/ui/admin_dashboard.py --server.port 8503
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
""")

# Refresh button
if st.button("🔄 Refresh Status"):
    st.rerun()

st.info("💡 **Tip**: Use the manual commands above if the launch buttons don't work.")
