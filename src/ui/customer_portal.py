"""
Customer Portal - Main KYC Interface
Modern Streamlit-based portal for customer onboarding and document management
"""
import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, date
from typing import Dict, Any, Optional
import uuid
import io
from PIL import Image
import base64

# Configure Streamlit
st.set_page_config(
    page_title="KYC Customer Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
        margin: 2rem auto;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .main-header h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header p {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        opacity: 0.9;
        margin-bottom: 0;
    }
    
    /* Card styles */
    .status-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e1e8ed;
        margin: 1.5rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .status-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .status-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    
    .success-card {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #c3e6cb;
    }
    
    .success-card::before {
        background: linear-gradient(90deg, #28a745, #20c997);
    }
    
    .warning-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffeaa7;
    }
    
    .warning-card::before {
        background: linear-gradient(90deg, #ffc107, #fd7e14);
    }
    
    .danger-card {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #f5c6cb;
    }
    
    .danger-card::before {
        background: linear-gradient(90deg, #dc3545, #e74c3c);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        text-align: center;
        margin: 1rem;
        border: 1px solid #e1e8ed;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.15);
    }
    
    .metric-card h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .metric-card .metric-value {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    /* Upload zone */
    .upload-zone {
        border: 3px dashed #667eea;
        border-radius: 20px;
        padding: 3rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        margin: 2rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .upload-zone::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.5; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); }
    }
    
    .upload-zone:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.15);
    }
    
    .upload-zone h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #667eea;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
    }
    
    .upload-zone p {
        font-family: 'Inter', sans-serif;
        color: #6c757d;
        position: relative;
        z-index: 1;
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
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .css-1d391kg .stMarkdown {
        color: white;
    }
    
    /* Form styling */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e1e8ed;
        padding: 0.75rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stSelectbox > div > div > select {
        border-radius: 10px;
        border: 2px solid #e1e8ed;
        font-family: 'Inter', sans-serif;
    }
    
    /* Progress bars */
    .stProgress .st-bo {
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        border-radius: 10px 10px 0 0;
        padding: 1rem 2rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        border: 1px solid #e1e8ed;
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Alerts */
    .stAlert {
        border-radius: 15px;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        font-family: 'Inter', sans-serif;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        border-radius: 10px;
        border: 1px solid #e1e8ed;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }
    
    /* File uploader */
    .stFileUploader {
        background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
        border-radius: 15px;
        border: 2px dashed #667eea;
        padding: 2rem;
    }
    
    /* Metrics */
    .css-1xarl3l {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e1e8ed;
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
API_BASE_URL = "http://localhost:8000/api/v1"
WORKFLOW_API_BASE = "http://localhost:8000/api/v1/workflow"

class KYCPortalAPI:
    """API client for KYC portal"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and get token"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data={"username": email, "password": password}
            )
            return response.json() if response.status_code == 200 else {"error": "Authentication failed"}
        except Exception as e:
            return {"error": str(e)}
    
    def register_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register new customer"""
        try:
            response = self.session.post(f"{self.base_url}/customers", json=customer_data)
            return response.json() if response.status_code == 201 else {"error": "Registration failed"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer information"""
        try:
            response = self.session.get(f"{self.base_url}/customers/{customer_id}")
            return response.json() if response.status_code == 200 else {"error": "Customer not found"}
        except Exception as e:
            return {"error": str(e)}
    
    def upload_document(self, customer_id: str, file_data: bytes, filename: str, document_type: str) -> Dict[str, Any]:
        """Upload document"""
        try:
            files = {"file": (filename, file_data, "application/octet-stream")}
            data = {"customer_id": customer_id, "document_type": document_type}
            response = self.session.post(f"{API_BASE_URL}/upload-document", files=files, data=data)
            return response.json() if response.status_code == 200 else {"error": "Upload failed"}
        except Exception as e:
            return {"error": str(e)}
    
    def start_kyc_workflow(self, customer_id: str, priority: str = "normal") -> Dict[str, Any]:
        """Start KYC workflow"""
        try:
            payload = {"customer_id": customer_id, "priority": priority}
            response = self.session.post(f"{WORKFLOW_API_BASE}/start", json=payload)
            return response.json() if response.status_code == 200 else {"error": "Workflow start failed"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        try:
            response = self.session.get(f"{WORKFLOW_API_BASE}/status/{session_id}")
            return response.json() if response.status_code == 200 else {"error": "Status not found"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_risk_assessment(self, customer_id: str) -> Dict[str, Any]:
        """Get risk assessment"""
        try:
            response = self.session.get(f"{WORKFLOW_API_BASE}/risk-assessment/{customer_id}")
            return response.json() if response.status_code == 200 else {"error": "Assessment not found"}
        except Exception as e:
            return {"error": str(e)}

# Initialize API client
api_client = KYCPortalAPI(API_BASE_URL)

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'customer_id' not in st.session_state:
        st.session_state.customer_id = None
    if 'customer_data' not in st.session_state:
        st.session_state.customer_data = None
    if 'workflow_session_id' not in st.session_state:
        st.session_state.workflow_session_id = None

def show_header():
    """Display main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🏦 KYC Customer Portal</h1>
        <p>Secure Document Verification & Identity Management</p>
    </div>
    """, unsafe_allow_html=True)

def show_login_page():
    """Display login/registration page"""
    st.markdown("### Welcome to KYC Portal")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.markdown("#### Sign In to Your Account")
        with st.form("login_form"):
            email = st.text_input("Email Address", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Sign In", use_container_width=True):
                if email and password:
                    # For demo, simulate authentication
                    st.session_state.authenticated = True
                    st.session_state.customer_id = str(uuid.uuid4())
                    st.success("✅ Successfully logged in!")
                    st.rerun()
                else:
                    st.error("Please enter both email and password")
    
    with tab2:
        st.markdown("#### Create New Account")
        show_registration_form()

def show_registration_form():
    """Display customer registration form"""
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name*", placeholder="John")
            last_name = st.text_input("Last Name*", placeholder="Doe")
            email = st.text_input("Email Address*", placeholder="john.doe@example.com")
            phone = st.text_input("Phone Number", placeholder="+1234567890")
        
        with col2:
            date_of_birth = st.date_input("Date of Birth*", max_value=date.today())
            nationality = st.selectbox("Nationality", ["US", "CA", "GB", "DE", "FR", "Other"])
            country = st.selectbox("Country of Residence", ["United States", "Canada", "United Kingdom", "Germany", "France", "Other"])
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
        
        st.markdown("#### Address Information")
        address_line_1 = st.text_input("Address Line 1*", placeholder="123 Main Street")
        col3, col4 = st.columns(2)
        with col3:
            city = st.text_input("City*", placeholder="New York")
            state = st.text_input("State/Province", placeholder="NY")
        with col4:
            postal_code = st.text_input("Postal Code", placeholder="10001")
        
        terms_accepted = st.checkbox("I agree to the Terms of Service and Privacy Policy*")
        
        if st.form_submit_button("Create Account", use_container_width=True):
            if first_name and last_name and email and date_of_birth and address_line_1 and city and terms_accepted:
                customer_data = {
                    "id": str(uuid.uuid4()),
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "date_of_birth": date_of_birth.isoformat(),
                    "nationality": nationality,
                    "country": country,
                    "gender": gender,
                    "address_line_1": address_line_1,
                    "city": city,
                    "state": state,
                    "postal_code": postal_code
                }
                
                # For demo, simulate successful registration
                st.session_state.authenticated = True
                st.session_state.customer_id = customer_data["id"]
                st.session_state.customer_data = customer_data
                st.success("✅ Account created successfully! Welcome to KYC Portal.")
                st.rerun()
            else:
                st.error("Please fill in all required fields (*) and accept the terms")

def show_dashboard():
    """Display main customer dashboard"""
    if not st.session_state.customer_data:
        # Create mock customer data for demo
        st.session_state.customer_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "kyc_status": "pending_verification"
        }
    
    customer = st.session_state.customer_data
    
    # Welcome message
    st.markdown(f"### Welcome back, {customer['first_name']} {customer['last_name']}! 👋")
    
    # KYC Status Overview
    show_kyc_status_overview()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Document Upload", "📊 KYC Status", "⚠️ Risk Assessment", "👤 Profile"])
    
    with tab1:
        show_document_upload()
    
    with tab2:
        show_kyc_status_detail()
    
    with tab3:
        show_risk_assessment()
    
    with tab4:
        show_profile_management()

def show_kyc_status_overview():
    """Display KYC status overview cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #007bff; margin: 0;">📋 KYC Status</h3>
            <p style="font-size: 1.2em; margin: 0.5rem 0;"><strong>Under Review</strong></p>
            <small>Last updated: Today</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #28a745; margin: 0;">📄 Documents</h3>
            <p style="font-size: 1.2em; margin: 0.5rem 0;"><strong>2 / 3</strong></p>
            <small>1 pending upload</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #ffc107; margin: 0;">⚠️ Risk Level</h3>
            <p style="font-size: 1.2em; margin: 0.5rem 0;"><strong>Medium</strong></p>
            <small>Additional verification needed</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #17a2b8; margin: 0;">⏱️ Processing Time</h3>
            <p style="font-size: 1.2em; margin: 0.5rem 0;"><strong>2-3 days</strong></p>
            <small>Estimated completion</small>
        </div>
        """, unsafe_allow_html=True)

def show_document_upload():
    """Display document upload interface"""
    st.markdown("### 📄 Document Upload Center")
    
    # Document requirements
    with st.expander("📋 Required Documents", expanded=True):
        st.markdown("""
        **Please upload the following documents for identity verification:**
        
        1. **Government-issued ID** (Passport, Driver's License, or National ID)
        2. **Proof of Address** (Utility bill, Bank statement - max 3 months old)
        3. **Additional Verification** (If required based on risk assessment)
        
        **File Requirements:**
        - Formats: PDF, JPG, PNG
        - Max size: 10MB per file
        - Clear, readable images
        - All corners visible
        """)
    
    # Document upload form
    document_types = {
        "passport": "🛂 Passport",
        "drivers_license": "🚗 Driver's License", 
        "national_id": "🆔 National ID",
        "utility_bill": "⚡ Utility Bill",
        "bank_statement": "🏦 Bank Statement",
        "other": "📎 Other Document"
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_doc_type = st.selectbox("Document Type", options=list(document_types.keys()), 
                                        format_func=lambda x: document_types[x])
        
        uploaded_file = st.file_uploader(
            "Choose file", 
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Upload a clear image or PDF of your document"
        )
        
        if uploaded_file:
            st.markdown(f"**File:** {uploaded_file.name}")
            st.markdown(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
            st.markdown(f"**Type:** {uploaded_file.type}")
            
            # Preview for images
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                st.image(image, width=300, caption="Document Preview")
            
            if st.button("🚀 Upload Document", use_container_width=True):
                with st.spinner("Uploading document..."):
                    # Simulate upload
                    progress = st.progress(0)
                    for i in range(100):
                        progress.progress(i + 1)
                    
                    st.success(f"✅ {document_types[selected_doc_type]} uploaded successfully!")
                    st.info("🔄 Document is being processed and verified...")
    
    with col2:
        st.markdown("### 📋 Upload Status")
        
        # Mock uploaded documents
        documents = [
            {"name": "Passport", "status": "✅ Verified", "uploaded": "2 hours ago"},
            {"name": "Utility Bill", "status": "🔄 Processing", "uploaded": "1 hour ago"},
            {"name": "Additional ID", "status": "❌ Required", "uploaded": "Not uploaded"}
        ]
        
        for doc in documents:
            status_class = "success-card" if "✅" in doc["status"] else "warning-card" if "🔄" in doc["status"] else "danger-card"
            st.markdown(f"""
            <div class="status-card {status_class}">
                <strong>{doc['name']}</strong><br>
                Status: {doc['status']}<br>
                <small>{doc['uploaded']}</small>
            </div>
            """, unsafe_allow_html=True)

def show_kyc_status_detail():
    """Display detailed KYC status and workflow progress"""
    st.markdown("### 📊 KYC Verification Progress")
    
    # Workflow steps
    steps = [
        {"name": "Document Upload", "status": "completed", "description": "Upload required documents"},
        {"name": "Document Analysis", "status": "completed", "description": "AI-powered document verification"},
        {"name": "Identity Verification", "status": "in_progress", "description": "Cross-reference identity information"},
        {"name": "Risk Assessment", "status": "pending", "description": "Evaluate risk factors"},
        {"name": "Compliance Check", "status": "pending", "description": "Regulatory compliance verification"},
        {"name": "Final Review", "status": "pending", "description": "Manual review if required"}
    ]
    
    for i, step in enumerate(steps, 1):
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if step["status"] == "completed":
                st.markdown("✅")
            elif step["status"] == "in_progress":
                st.markdown("🔄")
            else:
                st.markdown("⏳")
        
        with col2:
            status_text = step["status"].replace("_", " ").title()
            st.markdown(f"**{i}. {step['name']}** - *{status_text}*")
            st.markdown(f"<small>{step['description']}</small>", unsafe_allow_html=True)
        
        with col3:
            if step["status"] == "completed":
                st.markdown("✅ Done")
            elif step["status"] == "in_progress":
                st.markdown("🔄 Active")
            else:
                st.markdown("⏳ Waiting")
        
        if i < len(steps):
            st.markdown("---")
    
    # Estimated completion
    st.markdown("### ⏱️ Timeline Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Estimated Completion:** 2-3 business days")
        st.info("**Current Step:** Identity Verification")
    
    with col2:
        st.info("**Processing Priority:** Normal")
        st.info("**Started:** Today at 2:30 PM")

def show_risk_assessment():
    """Display risk assessment information"""
    st.markdown("### ⚠️ Risk Assessment Summary")
    
    # Risk level indicator
    risk_level = "Medium"
    risk_score = 0.45
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Risk gauge
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #ffc107;">Risk Level</h3>
            <h2 style="color: #ffc107; margin: 0;">{risk_level}</h2>
            <p>Score: {risk_score:.2f}/1.00</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Risk Factors Identified")
        risk_factors = [
            {"factor": "Geographic Risk", "level": "Low", "details": "Country of residence: Low risk jurisdiction"},
            {"factor": "Document Quality", "level": "Medium", "details": "Some documents require enhancement"},
            {"factor": "Identity Verification", "level": "Low", "details": "Primary documents verified successfully"},
            {"factor": "Behavioral Patterns", "level": "Low", "details": "Normal submission patterns detected"}
        ]
        
        for factor in risk_factors:
            color = "#28a745" if factor["level"] == "Low" else "#ffc107" if factor["level"] == "Medium" else "#dc3545"
            st.markdown(f"""
            <div style="border-left: 3px solid {color}; padding-left: 10px; margin: 10px 0;">
                <strong>{factor['factor']}</strong> - <span style="color: {color};">{factor['level']} Risk</span><br>
                <small>{factor['details']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Recommendations
    st.markdown("#### 💡 Recommendations")
    recommendations = [
        "Upload high-quality scans of all documents",
        "Ensure all document corners are visible and text is readable",
        "Verify that personal information matches across all documents"
    ]
    
    for rec in recommendations:
        st.markdown(f"• {rec}")

def show_profile_management():
    """Display profile management interface"""
    st.markdown("### 👤 Profile Management")
    
    if st.session_state.customer_data:
        customer = st.session_state.customer_data
        
        # Profile information
        with st.form("profile_form"):
            st.markdown("#### Personal Information")
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name", value=customer.get("first_name", ""))
                last_name = st.text_input("Last Name", value=customer.get("last_name", ""))
                email = st.text_input("Email", value=customer.get("email", ""))
            
            with col2:
                phone = st.text_input("Phone", value=customer.get("phone", ""))
                nationality = st.text_input("Nationality", value=customer.get("nationality", ""))
                country = st.text_input("Country", value=customer.get("country", ""))
            
            st.markdown("#### Preferences")
            email_notifications = st.checkbox("Email notifications", value=True)
            sms_notifications = st.checkbox("SMS notifications", value=False)
            
            col3, col4 = st.columns(2)
            with col3:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    st.success("✅ Profile updated successfully!")
            
            with col4:
                if st.form_submit_button("🔐 Change Password", use_container_width=True):
                    st.info("Password change form would appear here")

def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.markdown("### 🏦 KYC Portal")
        
        if st.session_state.authenticated:
            st.markdown(f"**Welcome,** {st.session_state.customer_data.get('first_name', 'User')}!")
            
            st.markdown("---")
            
            # Quick actions
            st.markdown("#### Quick Actions")
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.rerun()
            
            if st.button("📞 Contact Support", use_container_width=True):
                st.info("Support: support@kycportal.com\nPhone: +1-800-KYC-HELP")
            
            st.markdown("---")
            
            # Account actions
            if st.button("🚪 Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        else:
            st.markdown("#### About KYC Portal")
            st.markdown("""
            Secure, fast, and compliant identity verification platform.
            
            **Features:**
            - AI-powered document analysis
            - Real-time status updates  
            - Bank-grade security
            - 24/7 support
            """)

def main():
    """Main application entry point"""
    init_session_state()
    show_header()
    show_sidebar()
    
    if st.session_state.authenticated:
        show_dashboard()
    else:
        show_login_page()

if __name__ == "__main__":
    main()
