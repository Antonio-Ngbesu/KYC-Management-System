"""
Database initialization and setup
"""
from database.config import Base, engine, database
from database.models import *  # Import all models


def init_database():
    """Initialize database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def reset_database():
    """Reset database (DROP and CREATE all tables)"""
    print("⚠️  WARNING: This will delete all data!")
    response = input("Are you sure you want to reset the database? (yes/NO): ")
    
    if response.lower() == 'yes':
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        print("Database reset complete!")
    else:
        print("Database reset cancelled.")


async def startup_database():
    """Startup database connection (for FastAPI)"""
    await database.connect()
    print("Database connected successfully!")


async def shutdown_database():
    """Shutdown database connection (for FastAPI)"""
    await database.disconnect()
    print("Database disconnected.")


if __name__ == "__main__":
    # Allow running this script directly to initialize database
    init_database()
