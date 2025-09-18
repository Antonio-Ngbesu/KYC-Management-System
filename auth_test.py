"""
Simple Authentication Test
Test the development authentication system
"""
import streamlit as st
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from src.auth.dev_auth import show_login_form, show_user_info, dev_auth, require_auth
    AUTH_AVAILABLE = True
except ImportError as e:
    st.error(f"Authentication module import failed: {e}")
    AUTH_AVAILABLE = False

def main():
    st.set_page_config(
        page_title="KYC Auth Test",
        page_icon="🔐",
        layout="wide"
    )
    
    # Custom CSS for better appearance
    st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔐 KYC Authentication Test")
    
    # Show user info if authenticated
    if AUTH_AVAILABLE and dev_auth.is_authenticated():
        show_user_info()
        
        st.markdown("---")
        st.success("✅ Authentication successful!")
        
        user = dev_auth.get_current_user()
        
        # Show user details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("User", user['name'])
        
        with col2:
            st.metric("Role", user['role'].title())
        
        with col3:
            st.metric("Status", "Active")
        
        # Show role-specific content
        st.markdown("### Role-Specific Access")
        
        if user['role'] == 'customer':
            st.info("🏪 Customer Portal - Upload documents and track KYC status")
            if st.button("🚀 Launch Customer Portal"):
                st.success("Would redirect to customer portal")
                
        elif user['role'] == 'analyst':
            st.info("🔍 Analyst Dashboard - Review and approve KYC documents")
            if st.button("🚀 Launch Analyst Dashboard"):
                st.success("Would redirect to analyst dashboard")
                
        elif user['role'] == 'admin':
            st.info("⚙️ Admin Dashboard - System administration and user management")
            if st.button("🚀 Launch Admin Dashboard"):
                st.success("Would redirect to admin dashboard")
        
        # Test different role access
        st.markdown("### Access Control Test")
        
        with st.expander("Test Role-Based Access"):
            st.markdown("**Current Role Access:**")
            
            if user['role'] == 'admin':
                st.success("✅ Admin access - Full system control")
                st.success("✅ Analyst access - Can review documents") 
                st.success("✅ Customer access - Can submit documents")
            elif user['role'] == 'analyst':
                st.warning("❌ Admin access - Restricted")
                st.success("✅ Analyst access - Can review documents")
                st.success("✅ Customer access - Can submit documents")
            else:
                st.warning("❌ Admin access - Restricted")
                st.warning("❌ Analyst access - Restricted")
                st.success("✅ Customer access - Can submit documents")
    
    else:
        # Show login form
        if AUTH_AVAILABLE:
            st.markdown("### Please login to continue")
            show_login_form()
        else:
            st.error("Authentication system is not available")
            st.info("Running in demo mode without authentication")

if __name__ == "__main__":
    main()
