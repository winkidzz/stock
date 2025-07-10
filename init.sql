-- Initialize PostgreSQL database for Stock Screener
-- This script runs during Docker container startup

-- Create the database if it doesn't exist
SELECT 'CREATE DATABASE stock_screener' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'stock_screener');

-- Connect to the database
\c stock_screener;

-- Create the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a user for the application (if needed)
-- CREATE USER stock_screener_user WITH PASSWORD 'your_password';
-- GRANT ALL PRIVILEGES ON DATABASE stock_screener TO stock_screener_user;

-- Set up initial configuration
SET timezone = 'UTC';

-- Create initial indexes for performance
-- These will be created by SQLAlchemy, but we can pre-create some for better performance

-- Example: Create partial indexes for active stocks
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stocks_active_symbol 
-- ON stocks(symbol) WHERE is_active = true;

-- Log the completion
SELECT 'Database initialization completed' AS status; 