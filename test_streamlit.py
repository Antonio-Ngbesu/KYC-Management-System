"""
Test Streamlit App - Minimal Version
"""
import streamlit as st

st.set_page_config(
    page_title="KYC System Test",
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
    }
</style>
""", unsafe_allow_html=True)

st.title("🏦 KYC System Test")
st.success("✅ Streamlit is working correctly!")

st.markdown("### System Status")
st.info("This is a test page to verify Streamlit functionality.")

if st.button("Test Button"):
    st.balloons()
    st.success("Button clicked successfully!")
