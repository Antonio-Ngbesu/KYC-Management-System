"""Simple test script to check if imports work"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append('src')

print("🧪 Testing KYC App imports...")

try:
    print("1. Testing environment loading...")
    from dotenv import load_dotenv
    load_dotenv()
    print(f"   ✅ DATABASE_URL: {os.getenv('DATABASE_URL', 'not found')}")
    
    print("2. Testing database config...")
    from database.config import DATABASE_URL, SessionLocal
    print(f"   ✅ Database configured: {DATABASE_URL}")
    
    print("3. Testing auth models...")
    from auth.models import User, UserRole
    print("   ✅ Auth models loaded")
    
    print("4. Testing JWT service...")
    from auth.jwt_service import jwt_manager
    print("   ✅ JWT manager loaded")
    
    print("5. Testing FastAPI app...")
    from api.main import app
    print("   ✅ FastAPI app loaded")
    
    print("\n🎉 All imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
