#!/usr/bin/env python3
"""
Database setup script for KYC Document Analyzer
Sets up PostgreSQL database and creates initial admin user
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from database.config import create_tables, SessionLocal
from database.repositories import get_user_repo
from auth.models import UserRole
import bcrypt


def setup_database():
    """Set up database tables"""
    print("🗄️  Setting up database...")
    
    try:
        create_tables()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        return False


def create_admin_user():
    """Create initial admin user"""
    print("\n👤 Creating admin user...")
    
    try:
        db = SessionLocal()
        user_repo = get_user_repo(db)
        
        # Check if admin already exists
        existing_admin = user_repo.get_user_by_username("admin")
        if existing_admin:
            print("⚠️  Admin user already exists!")
            return True
        
        # Get admin details
        print("\nEnter admin user details:")
        username = input("Username (default: admin): ").strip() or "admin"
        email = input("Email: ").strip()
        password = input("Password (min 8 chars): ").strip()
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters!")
            return False
        
        if not email:
            print("❌ Email is required!")
            return False
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create admin user
        admin_data = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "role": UserRole.ADMIN,
            "is_active": True,
            "is_verified": True,
            "department": "IT Administration"
        }
        
        admin_user = user_repo.create_user(admin_data)
        print(f"✅ Admin user created successfully! User ID: {admin_user.user_id}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        if 'db' in locals():
            db.close()
        return False


def check_database_connection():
    """Check if database connection works"""
    print("🔍 Checking database connection...")
    
    try:
        db = SessionLocal()
        # Try a simple query
        db.execute("SELECT 1")
        db.close()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL in .env file")
        print("3. Ensure the database exists and user has permissions")
        return False


def main():
    """Main setup function"""
    print("🚀 KYC Document Analyzer - Database Setup")
    print("=" * 50)
    
    # Check environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables!")
        print("Please copy .env.example to .env and configure your database URL")
        return False
    
    print(f"Database URL: {database_url}")
    
    # Check database connection
    if not check_database_connection():
        return False
    
    # Setup database tables
    if not setup_database():
        return False
    
    # Create admin user
    create_admin = input("\nCreate admin user? (Y/n): ").strip().lower()
    if create_admin != 'n':
        if not create_admin_user():
            return False
    
    print("\n" + "=" * 50)
    print("🎉 Database setup completed successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Start your API server: uvicorn src.api.main:app --reload")
    print("2. Visit http://localhost:8000/docs for API documentation")
    print("3. Login with your admin credentials")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
