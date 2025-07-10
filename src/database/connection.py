from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from contextlib import contextmanager
import logging
from typing import Generator

from ..config import settings
from .models import Base

logger = logging.getLogger(__name__)

# Synchronous database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Async database engine
async_engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    bind=async_engine,
)

def create_tables():
    """Create all database tables"""
    try:
        # Enable pgvector extension
        with engine.connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            connection.commit()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def drop_tables():
    """Drop all database tables (use with caution)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

async def get_async_db_session() -> AsyncSession:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Async database session error: {e}")
            raise
        finally:
            await session.close()

def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check function
def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Initialize database function
def init_database():
    """Initialize database with tables and extensions"""
    try:
        logger.info("Initializing database...")
        
        # Create tables
        create_tables()
        
        # Verify connection
        if check_database_health():
            logger.info("Database initialized successfully")
        else:
            raise Exception("Database health check failed after initialization")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    # For testing purposes
    init_database() 