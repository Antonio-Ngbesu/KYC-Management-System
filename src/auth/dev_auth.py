"""
Development Authentication Bypass
Simple authentication for development and testing without 2FA
"""
import streamlit as st
from typing import Dict, Any, Optional
import requests
import json

# Default development users
DEV_USERS = {
    "customer@demo.com": {
        "password": "demo123",
        "role": "customer",
        "name": "Demo Customer"
    },
    "analyst@demo.com": {
        "password": "demo123", 
        "role": "analyst",
        "name": "Demo Analyst"
    },
    "admin@demo.com": {
        "password": "demo123",
        "role": "admin", 
        "name": "Demo Admin"
    }
}

class DevAuth:
    """Development authentication system"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Simple login without 2FA"""
        # Check development users first
        if username in DEV_USERS:
            dev_user = DEV_USERS[username]
            if password == dev_user["password"]:
                return {
                    "success": True,
                    "token": f"dev_token_{username}",
                    "user": {
                        "username": username,
                        "role": dev_user["role"],
                        "name": dev_user["name"]
                    }
                }
        
        # Try API authentication (without 2FA)
        try:
            response = requests.post(
                f"{self.api_base}/auth/login",
                json={"username": username, "password": password},
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    **response.json()
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid credentials"
                }
                
        except requests.exceptions.RequestException:
            # API not available, fall back to dev users
            return {
                "success": False,
                "error": "Authentication service unavailable"
            }
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return "auth_token" in st.session_state and st.session_state.auth_token is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        if self.is_authenticated():
            return st.session_state.get("current_user")
        return None
    
    def logout(self):
        """Logout current user"""
        if "auth_token" in st.session_state:
            del st.session_state.auth_token
        if "current_user" in st.session_state:
            del st.session_state.current_user

# Global auth instance
dev_auth = DevAuth()

def show_login_form():
    """Show simple login form without 2FA"""
    st.markdown("""
    <div style="max-width: 400px; margin: 2rem auto; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="text-align: center; color: #667eea; margin-bottom: 2rem;">🏦 KYC System Login</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        st.markdown("### Enter your credentials")
        
        username = st.text_input("Email/Username", placeholder="user@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        # Demo credentials info
        with st.expander("💡 Demo Credentials"):
            st.markdown("""
            **Development Users:**
            - **Customer**: `customer@demo.com` / `demo123`
            - **Analyst**: `analyst@demo.com` / `demo123` 
            - **Admin**: `admin@demo.com` / `demo123`
            """)
        
        submitted = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("Please enter both username and password")
                return False
            
            with st.spinner("Authenticating..."):
                result = dev_auth.login(username, password)
                
                if result["success"]:
                    # Store authentication state
                    st.session_state.auth_token = result.get("token")
                    st.session_state.current_user = result.get("user")
                    
                    st.success(f"✅ Welcome, {result['user']['name']}!")
                    st.rerun()
                    return True
                else:
                    st.error(f"❌ Login failed: {result.get('error', 'Unknown error')}")
                    return False
    
    return False

def require_auth(required_role: str = None):
    """Decorator to require authentication"""
    if not dev_auth.is_authenticated():
        st.warning("🔒 Please login to access this page")
        show_login_form()
        st.stop()
    
    user = dev_auth.get_current_user()
    if required_role and user.get("role") != required_role:
        st.error(f"❌ Access denied. Required role: {required_role}")
        st.stop()
    
    return user

def show_user_info():
    """Show current user info and logout button"""
    if dev_auth.is_authenticated():
        user = dev_auth.get_current_user()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"👤 Logged in as: **{user['name']}** ({user['role']})")
        
        with col2:
            if st.button("🚪 Logout"):
                dev_auth.logout()
                st.rerun()

# Utility functions for easy integration
def login_required(func):
    """Decorator for functions that require authentication"""
    def wrapper(*args, **kwargs):
        if not dev_auth.is_authenticated():
            show_login_form()
            return None
        return func(*args, **kwargs)
    return wrapper

def role_required(required_role: str):
    """Decorator for functions that require specific role"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = require_auth(required_role)
            return func(*args, **kwargs)
        return wrapper
    return decorator
