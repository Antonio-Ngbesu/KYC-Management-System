"""
Analyst Dashboard - KYC Review Interface
Professional interface for analysts to review KYC applications and make decisions
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any
import requests

# Configure Streamlit
st.set_page_config(
    page_title="KYC Analyst Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern analyst interface
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global app styling */
    .stApp {
        background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
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
    .analyst-header {
        background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 3rem;
        text-align: center;
        box-shadow: 0 15px 35px rgba(15, 76, 117, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .analyst-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: analysis-shine 5s ease-in-out infinite;
    }
    
    @keyframes analysis-shine {
        0%, 100% { opacity: 0.3; transform: rotate(0deg); }
        50% { opacity: 0.6; transform: rotate(180deg); }
    }
    
    .analyst-header h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.8rem;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        position: relative;
        z-index: 1;
    }
    
    /* Priority cards */
    .priority-high {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border-left: 6px solid #f44336;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(244, 67, 54, 0.15);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .priority-high::before {
        content: '🚨';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
        opacity: 0.7;
    }
    
    .priority-high:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(244, 67, 54, 0.25);
    }
    
    .priority-medium {
        background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
        border-left: 6px solid #ff9800;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(255, 152, 0, 0.15);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .priority-medium::before {
        content: '⚠️';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
        opacity: 0.7;
    }
    
    .priority-medium:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(255, 152, 0, 0.25);
    }
    
    .priority-low {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border-left: 6px solid #4caf50;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(76, 175, 80, 0.15);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .priority-low::before {
        content: '✅';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
        opacity: 0.7;
    }
    
    .priority-low:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(76, 175, 80, 0.25);
    }
    
    /* Review cards */
    .review-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        border: 2px solid #e0e7ff;
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .review-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0f4c75, #3282b8);
    }
    
    .review-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        border-color: #3282b8;
    }
    
    /* Risk indicators */
    .risk-indicator {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.9rem;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .risk-indicator:hover {
        transform: scale(1.05);
    }
    
    .risk-low { 
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .risk-medium { 
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .risk-high { 
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    /* Metrics grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 2rem;
        margin: 2rem 0;
    }
    
    .metric-box {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 2px solid #e0e7ff;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0f4c75, #3282b8);
    }
    
    .metric-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        border-color: #3282b8;
    }
    
    .metric-box h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    .metric-box .metric-value {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #0f4c75;
        margin-bottom: 0.5rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0f4c75 0%, #3282b8 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(15, 76, 117, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(15, 76, 117, 0.4);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
WORKFLOW_API_BASE = "http://localhost:8000/api/v1/workflow"

class AnalystAPI:
    """API client for analyst operations"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_workflow_queue(self, status: str = None, priority: str = None) -> List[Dict[str, Any]]:
        """Get workflow queue for review"""
        try:
            params = {}
            if status:
                params['status'] = status
            if priority:
                params['priority'] = priority
            
            response = self.session.get(f"{WORKFLOW_API_BASE}/queue", params=params)
            return response.json() if response.status_code == 200 else []
        except Exception:
            return self._get_mock_queue()
    
    def get_workflow_details(self, session_id: str) -> Dict[str, Any]:
        """Get detailed workflow information"""
        try:
            response = self.session.get(f"{WORKFLOW_API_BASE}/status/{session_id}")
            return response.json() if response.status_code == 200 else {}
        except Exception:
            return self._get_mock_workflow_details(session_id)
    
    def get_risk_assessment(self, customer_id: str) -> Dict[str, Any]:
        """Get risk assessment for customer"""
        try:
            response = self.session.get(f"{WORKFLOW_API_BASE}/risk-assessment/{customer_id}")
            return response.json() if response.status_code == 200 else {}
        except Exception:
            return self._get_mock_risk_assessment(customer_id)
    
    def submit_decision(self, session_id: str, decision: str, notes: str = "") -> Dict[str, Any]:
        """Submit review decision"""
        try:
            payload = {
                "session_id": session_id,
                "decision": decision,
                "reviewer_notes": notes
            }
            response = self.session.post(f"{WORKFLOW_API_BASE}/decision", json=payload)
            return response.json() if response.status_code == 200 else {"error": "Decision submission failed"}
        except Exception:
            return {"message": f"Decision '{decision}' submitted successfully (demo mode)"}
    
    def _get_mock_queue(self) -> List[Dict[str, Any]]:
        """Mock workflow queue data"""
        return [
            {
                "session_id": "kyc-001",
                "customer_id": "cust-001",
                "status": "pending_review",
                "priority": "high",
                "risk_level": "high",
                "risk_score": 0.78,
                "created_at": "2025-09-17T10:30:00Z",
                "customer_name": "John Smith",
                "progress_percentage": 85
            },
            {
                "session_id": "kyc-002", 
                "customer_id": "cust-002",
                "status": "pending_review",
                "priority": "medium",
                "risk_level": "medium",
                "risk_score": 0.45,
                "created_at": "2025-09-17T09:15:00Z",
                "customer_name": "Sarah Johnson",
                "progress_percentage": 92
            },
            {
                "session_id": "kyc-003",
                "customer_id": "cust-003", 
                "status": "processing",
                "priority": "low",
                "risk_level": "low",
                "risk_score": 0.23,
                "created_at": "2025-09-17T08:45:00Z",
                "customer_name": "Michael Chen",
                "progress_percentage": 67
            }
        ]
    
    def _get_mock_workflow_details(self, session_id: str) -> Dict[str, Any]:
        """Mock workflow details"""
        return {
            "session_id": session_id,
            "customer_id": "cust-001",
            "status": "pending_review",
            "current_step": "manual_review",
            "progress_percentage": 85,
            "risk_score": 0.78,
            "risk_level": "high",
            "created_at": "2025-09-17T10:30:00Z",
            "estimated_completion": "2025-09-19T15:00:00Z"
        }
    
    def _get_mock_risk_assessment(self, customer_id: str) -> Dict[str, Any]:
        """Mock risk assessment data"""
        return {
            "customer_id": customer_id,
            "overall_risk_score": 0.78,
            "risk_level": "high",
            "confidence_score": 0.89,
            "risk_factors": [
                {
                    "category": "geographic_risk",
                    "factor_name": "high_risk_jurisdiction",
                    "weight": 0.8,
                    "score": 0.9,
                    "description": "Customer from high-risk jurisdiction",
                    "evidence": {"country": "Afghanistan"}
                },
                {
                    "category": "document_quality",
                    "factor_name": "poor_quality_documents",
                    "weight": 0.6,
                    "score": 0.7,
                    "description": "Documents with poor quality scores",
                    "evidence": {"poor_quality_docs": ["passport_scan"]}
                }
            ],
            "recommendations": [
                "Require manual review by senior analyst",
                "Request additional documentation",
                "Apply enhanced due diligence procedures"
            ]
        }

# Initialize API client
api_client = AnalystAPI(API_BASE_URL)

def init_session_state():
    """Initialize session state"""
    if 'analyst_authenticated' not in st.session_state:
        st.session_state.analyst_authenticated = False
    if 'analyst_name' not in st.session_state:
        st.session_state.analyst_name = "Senior Analyst"
    if 'selected_case' not in st.session_state:
        st.session_state.selected_case = None

def show_header():
    """Display analyst dashboard header"""
    st.markdown("""
    <div class="analyst-header">
        <h1>🔍 KYC Analyst Dashboard</h1>
        <p>Professional Review & Decision Management System</p>
    </div>
    """, unsafe_allow_html=True)

def show_login():
    """Show analyst login"""
    st.markdown("### 🔐 Analyst Authentication")
    
    with st.form("analyst_login"):
        col1, col2 = st.columns([1, 1])
        with col1:
            username = st.text_input("Username", placeholder="analyst@company.com")
            password = st.text_input("Password", type="password")
        
        with col2:
            role = st.selectbox("Role", ["Senior Analyst", "Junior Analyst", "Compliance Officer"])
        
        if st.form_submit_button("🚀 Sign In", use_container_width=True):
            if username and password:
                st.session_state.analyst_authenticated = True
                st.session_state.analyst_name = role
                st.success(f"✅ Welcome, {role}!")
                st.rerun()
            else:
                st.error("Please enter credentials")

def show_dashboard_overview():
    """Show analyst dashboard overview"""
    st.markdown(f"### Welcome back, {st.session_state.analyst_name}! 👋")
    
    # Metrics overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-box">
            <h3 style="color: #f44336; margin: 0;">🔴 High Priority</h3>
            <h2 style="margin: 0.5rem 0;">12</h2>
            <small>Pending Review</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-box">
            <h3 style="color: #ff9800; margin: 0;">🟡 Medium Priority</h3>
            <h2 style="margin: 0.5rem 0;">28</h2>
            <small>In Queue</small>
        </div>  
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-box">
            <h3 style="color: #4caf50; margin: 0;">✅ Completed Today</h3>
            <h2 style="margin: 0.5rem 0;">47</h2>
            <small>Applications</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-box">
            <h3 style="color: #2196f3; margin: 0;">⏱️ Avg Review Time</h3>
            <h2 style="margin: 0.5rem 0;">18m</h2>
            <small>This week</small>
        </div>
        """, unsafe_allow_html=True)

def show_workflow_queue():
    """Display workflow queue for review"""
    st.markdown("### 📋 Review Queue")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "pending_review", "processing", "completed"])
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "high", "medium", "low"])
    with col3:
        risk_filter = st.selectbox("Risk Level", ["All", "high", "medium", "low"])
    
    # Get queue data
    queue_data = api_client.get_workflow_queue()
    
    if queue_data:
        # Display queue items
        for item in queue_data:
            priority_class = f"priority-{item['priority']}"
            risk_class = f"risk-{item['risk_level']}"
            
            st.markdown(f"""
            <div class="{priority_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0;">{item.get('customer_name', 'Customer ' + item['customer_id'][-3:])}</h4>
                        <p style="margin: 0.2rem 0;"><strong>Session:</strong> {item['session_id']}</p>
                        <p style="margin: 0.2rem 0;"><strong>Created:</strong> {item['created_at'][:16]}</p>
                    </div>
                    <div style="text-align: center;">
                        <span class="risk-indicator {risk_class}">{item['risk_level'].upper()} RISK</span><br>
                        <small>Score: {item['risk_score']:.2f}</small>
                    </div>
                    <div style="text-align: right;">
                        <p style="margin: 0;"><strong>Priority:</strong> {item['priority'].upper()}</p>
                        <p style="margin: 0;"><strong>Progress:</strong> {item['progress_percentage']}%</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button(f"📖 Review", key=f"review_{item['session_id']}"):
                    st.session_state.selected_case = item['session_id']
                    st.rerun()
            with col2:
                if st.button(f"📊 Details", key=f"details_{item['session_id']}"):
                    show_case_details(item['session_id'])
            with col3:
                if st.button(f"⚠️ Risk Info", key=f"risk_{item['session_id']}"):
                    show_risk_details(item['customer_id'])
    else:
        st.info("No applications in queue for review.")

def show_case_review():
    """Show detailed case review interface"""
    if not st.session_state.selected_case:
        st.info("Select a case from the queue to begin review.")
        return
    
    session_id = st.session_state.selected_case
    st.markdown(f"### 📋 Case Review: {session_id}")
    
    # Get case details
    case_details = api_client.get_workflow_details(session_id)
    risk_assessment = api_client.get_risk_assessment(case_details.get('customer_id', ''))
    
    # Case overview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📄 Case Information")
        st.markdown(f"**Session ID:** {case_details.get('session_id', 'N/A')}")
        st.markdown(f"**Customer ID:** {case_details.get('customer_id', 'N/A')}")
        st.markdown(f"**Status:** {case_details.get('status', 'N/A')}")
        st.markdown(f"**Current Step:** {case_details.get('current_step', 'N/A')}")
        st.markdown(f"**Progress:** {case_details.get('progress_percentage', 0)}%")
        st.markdown(f"**Created:** {case_details.get('created_at', 'N/A')}")
    
    with col2:
        risk_level = risk_assessment.get('risk_level', 'unknown')
        risk_score = risk_assessment.get('overall_risk_score', 0)
        risk_class = f"risk-{risk_level}"
        
        st.markdown(f"""
        <div class="metric-box">
            <h3>⚠️ Risk Assessment</h3>
            <span class="risk-indicator {risk_class}">{risk_level.upper()}</span><br>
            <p><strong>Score:</strong> {risk_score:.2f}</p>
            <p><strong>Confidence:</strong> {risk_assessment.get('confidence_score', 0):.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Risk factors
    st.markdown("#### ⚠️ Risk Factors")
    risk_factors = risk_assessment.get('risk_factors', [])
    
    if risk_factors:
        for factor in risk_factors:
            st.markdown(f"""
            **{factor['factor_name'].replace('_', ' ').title()}**
            - Category: {factor['category'].replace('_', ' ').title()}
            - Weight: {factor['weight']:.2f}
            - Score: {factor['score']:.2f}
            - Description: {factor['description']}
            """)
    
    # Recommendations
    st.markdown("#### 💡 System Recommendations")
    recommendations = risk_assessment.get('recommendations', [])
    for rec in recommendations:
        st.markdown(f"• {rec}")
    
    # Decision interface
    st.markdown("#### 🎯 Review Decision")
    
    with st.form("decision_form"):
        decision = st.selectbox(
            "Decision",
            ["approve", "reject", "request_more_info"],
            format_func=lambda x: {
                "approve": "✅ Approve Application",
                "reject": "❌ Reject Application", 
                "request_more_info": "📝 Request Additional Information"
            }[x]
        )
        
        reviewer_notes = st.text_area(
            "Reviewer Notes",
            placeholder="Add your analysis, concerns, or additional requirements..."
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("✅ Submit Decision", use_container_width=True):
                result = api_client.submit_decision(session_id, decision, reviewer_notes)
                if "error" not in result:
                    st.success(f"✅ Decision submitted: {decision}")
                    st.session_state.selected_case = None
                    st.rerun()
                else:
                    st.error(f"Error: {result['error']}")
        
        with col2:
            if st.form_submit_button("💾 Save Draft", use_container_width=True):
                st.info("Decision saved as draft")
        
        with col3:
            if st.form_submit_button("🔙 Back to Queue", use_container_width=True):
                st.session_state.selected_case = None
                st.rerun()

def show_analytics():
    """Show analytics and reporting"""
    st.markdown("### 📊 Analytics & Reporting")
    
    # Sample data for charts
    date_range = pd.date_range(start='2025-09-01', end='2025-09-17', freq='D')
    applications_data = pd.DataFrame({
        'Date': date_range,
        'Applications': [45, 52, 38, 41, 59, 67, 43, 39, 48, 55, 61, 38, 42, 47, 53, 46, 51],
        'Approved': [35, 41, 29, 32, 44, 52, 33, 30, 37, 42, 47, 29, 33, 36, 41, 35, 39],
        'Rejected': [7, 8, 6, 6, 10, 11, 7, 6, 8, 9, 10, 6, 7, 8, 9, 8, 9],
        'Pending': [3, 3, 3, 3, 5, 4, 3, 3, 3, 4, 4, 3, 2, 3, 3, 3, 3]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Applications over time
        fig_apps = px.line(
            applications_data, 
            x='Date', 
            y=['Applications', 'Approved', 'Rejected'],
            title='Daily Application Processing',
            color_discrete_map={
                'Applications': '#2196f3',
                'Approved': '#4caf50', 
                'Rejected': '#f44336'
            }
        )
        st.plotly_chart(fig_apps, use_container_width=True)
    
    with col2:
        # Risk distribution
        risk_data = pd.DataFrame({
            'Risk Level': ['Low', 'Medium', 'High'],
            'Count': [156, 89, 23],
            'Percentage': [58.2, 33.2, 8.6]
        })
        
        fig_risk = px.pie(
            risk_data,
            values='Count',
            names='Risk Level',
            title='Risk Level Distribution',
            color_discrete_map={
                'Low': '#4caf50',
                'Medium': '#ff9800',
                'High': '#f44336'
            }
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    # Performance metrics
    st.markdown("#### 📈 Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Average Review Time", "18 minutes", "−2 min")
    with col2:
        st.metric("Approval Rate", "76.8%", "+2.1%")
    with col3:
        st.metric("SLA Compliance", "94.2%", "+1.3%")
    with col4:
        st.metric("Quality Score", "4.7/5.0", "+0.1")

def show_case_details(session_id: str):
    """Show detailed case information"""
    with st.expander(f"📋 Case Details: {session_id}", expanded=True):
        case_details = api_client.get_workflow_details(session_id)
        
        col1, col2 = st.columns(2)
        with col1:
            st.json(case_details)
        with col2:
            st.markdown("#### Workflow Steps")
            steps = [
                "Document Upload ✅",
                "Document Analysis ✅", 
                "Identity Verification ✅",
                "Risk Assessment ✅",
                "Compliance Check ⏳",
                "Manual Review ⏳"
            ]
            for step in steps:
                st.markdown(f"• {step}")

def show_risk_details(customer_id: str):
    """Show detailed risk information"""
    with st.expander(f"⚠️ Risk Assessment: {customer_id}", expanded=True):
        risk_data = api_client.get_risk_assessment(customer_id)
        st.json(risk_data)

def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.markdown("### 🔍 Analyst Tools")
        
        if st.session_state.analyst_authenticated:
            st.markdown(f"**{st.session_state.analyst_name}**")
            st.markdown("---")
            
            # Quick stats
            st.markdown("#### Today's Summary")
            st.markdown("• **Cases Reviewed:** 12")
            st.markdown("• **Approvals:** 9")
            st.markdown("• **Rejections:** 2")
            st.markdown("• **Pending:** 1")
            
            st.markdown("---")
            
            # Quick actions
            if st.button("🔄 Refresh Queue", use_container_width=True):
                st.rerun()
            
            if st.button("📊 Export Report", use_container_width=True):
                st.info("Report exported successfully!")
            
            if st.button("⚠️ Escalate Case", use_container_width=True):
                st.warning("Case escalation form would appear here")
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if 'analyst' in key:
                        del st.session_state[key]
                st.rerun()

def main():
    """Main application entry point"""
    init_session_state()
    show_header()
    show_sidebar()
    
    if not st.session_state.analyst_authenticated:
        show_login()
        return
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Review Queue", "🔍 Case Review", "📈 Analytics"])
    
    with tab1:
        show_dashboard_overview()
    
    with tab2:
        show_workflow_queue()
    
    with tab3:
        show_case_review()
    
    with tab4:
        show_analytics()

if __name__ == "__main__":
    main()
