#!/usr/bin/env python3
"""
Local development runner for Stock Screener Application
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if environment is set up correctly"""
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        logger.warning("No .env file found. Creating from .env.example...")
        try:
            with open(".env.example", "r") as example, open(".env", "w") as env:
                env.write(example.read())
            logger.info("Created .env file from .env.example")
            logger.info("Please edit .env file with your API keys")
        except FileNotFoundError:
            logger.error(".env.example not found. Please create .env file manually")
            return False
    
    # Check required environment variables
    required_vars = ["DATABASE_URL"]
    missing_vars = []
    
    from dotenv import load_dotenv
    load_dotenv()
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work without these variables")
    
    return True

def check_database():
    """Check if database is accessible"""
    try:
        from src.database import check_database_health
        if check_database_health():
            logger.info("Database connection successful")
            return True
        else:
            logger.error("Database connection failed")
            return False
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        logger.info("You may need to start PostgreSQL or run docker-compose up postgres")
        return False

def initialize_database():
    """Initialize database tables"""
    try:
        from src.database import init_database
        init_database()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def run_server():
    """Run the FastAPI server"""
    try:
        import uvicorn
        from src.main import app
        
        logger.info("Starting Stock Screener API server...")
        logger.info("API Documentation: http://localhost:8000/docs")
        logger.info("Health Check: http://localhost:8000/health")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        logger.error(f"Failed to import dependencies: {e}")
        logger.error("Please install dependencies: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")

def main():
    """Main function"""
    print("🚀 Stock Screener - Local Development Runner")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed")
        sys.exit(1)
    
    # Check database
    if not check_database():
        logger.error("Database check failed")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        # Initialize database
        if not initialize_database():
            logger.error("Database initialization failed")
            sys.exit(1)
    
    # Run server
    run_server()

if __name__ == "__main__":
    main() 