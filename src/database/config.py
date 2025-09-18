"""
Database configuration and connection management
"""
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# from databases import Database  # Temporarily disabled for testing
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://kyc_user:kyc_password@localhost:5432/kyc_database"
)

# Async database connection (don't connect during import)
database = None
engine = None

def initialize_database_connection():
    """Initialize database connection when needed"""
    global database, engine
    if database is None:
        try:
            # database = Database(DATABASE_URL)  # Disabled for now
            # SQLAlchemy setup - don't test connection during creation
            engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
            print(f"✅ Database configured: {DATABASE_URL}")
            return True
        except Exception as e:
            print(f"⚠️  Database configuration warning: {e}")
            database = None
            engine = None
            return False
    return True
def get_session_local():
    """Get SessionLocal, initializing connection if needed"""
    initialize_database_connection()
    if engine:
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return None

# For backwards compatibility
SessionLocal = get_session_local

# Base class for models
Base = declarative_base()

# Database metadata
metadata = MetaData()

async def connect_db():
    """Connect to database"""
    await database.connect()

async def disconnect_db():
    """Disconnect from database"""
    await database.disconnect()

def get_db():
    """Get database session (for dependency injection)"""
    SessionLocalFactory = get_session_local()
    if SessionLocalFactory:
        db = SessionLocalFactory()
        try:
            yield db
        finally:
            db.close()
    else:
        print("⚠️  No database session available")
        yield None

def create_tables():
    """Create all database tables"""
    initialize_database_connection()
    if engine:
        Base.metadata.create_all(bind=engine)
    else:
        print("⚠️  No database engine available")

def drop_tables():
    """Drop all database tables (use with caution!)"""
    if engine:
        Base.metadata.drop_all(bind=engine)
    else:
        print("⚠️  No database engine available")

def init_database():
    """Initialize database and create tables"""
    if not initialize_database_connection():
        print("⚠️  Database not configured - skipping initialization")
        return
        
    try:
        create_tables()
        
        # Create admin user if it doesn't exist
        from database.repositories import get_user_repo
        from auth.jwt_service import jwt_manager
        from auth.models import UserRole
        
        SessionLocalFactory = get_session_local()
        if not SessionLocalFactory:
            return
            
        db = SessionLocalFactory()
        try:
            user_repo = get_user_repo(db)
            
            # Check if admin exists
            admin = user_repo.get_user_by_username("admin")
            if not admin:
                # Create default admin
                admin_data = {
                    "username": "admin",
                    "email": "admin@kyc-analyzer.com",
                    "password_hash": jwt_manager.hash_password("admin123"),  # Change in production!
                    "first_name": "System",
                    "last_name": "Administrator",
                    "role": UserRole.ADMIN.value,
                    "is_active": True,
                    "is_verified": True,
                    "department": "IT Administration"
                }
                
                user_repo.create_user(admin_data)
                print("✅ Default admin user created (username: admin, password: admin123)")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        print("💡 You may need to run the database setup script manually")
