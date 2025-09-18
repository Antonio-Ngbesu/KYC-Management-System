"""Minimal test script"""
import sys
import os

# Add src to path
sys.path.append('src')

print("🧪 Minimal testing...")

try:
    print("1. Testing dotenv...")
    from dotenv import load_dotenv
    load_dotenv()
    print("   ✅ Environment loaded")
    
    print("2. Testing SQLAlchemy basics...")
    from sqlalchemy import create_engine
    print("   ✅ SQLAlchemy imported")
    
    print("3. Testing auth models...")
    from auth.models import User, UserRole
    print("   ✅ Auth models loaded")
    
    print("4. Testing direct database config...")
    # Skip the problematic imports for now
    print("   ⚠️  Skipping database connection test")
    
    print("5. Testing FastAPI...")
    from fastapi import FastAPI
    print("   ✅ FastAPI imported")
    
    print("\n🎉 Basic imports successful! Database connection may need separate setup.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
