import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "postgresql://username:password@localhost:5432/stock_screener"
    postgres_db: str = "stock_screener"
    postgres_user: str = "username"
    postgres_password: str = "password"
    
    # API Keys
    brave_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    
    # Local LLM Configuration
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "gemma3:27b"  # Primary model
    llm_model_fast: str = "llama3:8b"  # For faster operations
    llm_model_analysis: str = "deepseek-r1:70b"  # For complex analysis (optional)
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048
    
    # Application Settings
    app_name: str = "Stock Screener"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "your_secret_key_here"
    
    # Redis Configuration (optional)
    redis_url: str = "redis://localhost:6379"
    
    # Investment Parameters
    target_initial_investment: float = 10000.0
    target_final_amount: float = 2000000.0
    target_years: int = 10
    minimum_cagr: float = 0.349  # 34.9% required for 20x growth
    
    # API Rate Limits
    max_requests_per_minute: int = 60
    max_news_articles_per_stock: int = 10
    
    # Data Settings
    historical_data_years: int = 10
    update_frequency_minutes: int = 15
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Investment calculation functions
def calculate_required_cagr(initial: float, final: float, years: int) -> float:
    """Calculate required Compound Annual Growth Rate"""
    return (final / initial) ** (1 / years) - 1

def calculate_future_value(initial: float, cagr: float, years: int) -> float:
    """Calculate future value given initial investment, CAGR, and years"""
    return initial * (1 + cagr) ** years

# Default calculation for our target
REQUIRED_CAGR = calculate_required_cagr(
    settings.target_initial_investment,
    settings.target_final_amount,
    settings.target_years
) 