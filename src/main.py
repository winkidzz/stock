from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager
import asyncio

from .database import get_db, init_database, check_database_health, Stock, HistoricalData, FinancialMetrics, NewsArticle
from .config import settings, calculate_future_value, calculate_required_cagr
from .services.stock_data_service import stock_data_service
from .services.news_service import news_service
from .agents.data_collection_agent import data_collection_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Stock Screener Application")
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Check database health
    if not check_database_health():
        logger.error("Database health check failed")
        raise Exception("Database is not accessible")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Stock Screener Application")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered stock screener for finding high-growth investments",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
from pydantic import BaseModel

class StockRequest(BaseModel):
    symbol: str
    name: Optional[str] = None

class StockResponse(BaseModel):
    symbol: str
    name: str
    sector: str
    industry: str
    market_cap: float
    currency: str
    asset_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class HistoricalDataResponse(BaseModel):
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    dividend_amount: float

class FinancialMetricsResponse(BaseModel):
    date: datetime
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    roe: Optional[float]
    debt_to_equity: Optional[float]
    dividend_yield: Optional[float]
    earnings_per_share: Optional[float]

class NewsResponse(BaseModel):
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    relevance_score: Optional[float]

class GrowthProjection(BaseModel):
    initial_investment: float
    projected_value: float
    years: int
    required_cagr: float
    projected_cagr: float
    probability_of_success: float

# API Routes

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Stock Screener API is running",
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_health = check_database_health()
    return {
        "status": "healthy" if db_health else "unhealthy",
        "database": "connected" if db_health else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/stocks/add")
async def add_stock(
    stock_request: StockRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Add a new stock to the database and collect data"""
    symbol = stock_request.symbol.upper()
    
    # Check if stock already exists
    existing_stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if existing_stock:
        return {"message": f"Stock {symbol} already exists", "symbol": symbol}
    
    # Get stock name if not provided
    stock_name = stock_request.name
    if not stock_name:
        stock_info = stock_data_service.get_stock_info(symbol)
        if stock_info:
            stock_name = stock_info.name
        else:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Start background data collection
    background_tasks.add_task(
        collect_stock_data_background,
        symbol,
        stock_name
    )
    
    return {
        "message": f"Stock {symbol} added. Data collection started in background.",
        "symbol": symbol,
        "name": stock_name
    }

@app.get("/stocks/{symbol}")
async def get_stock(symbol: str, db: Session = Depends(get_db)):
    """Get stock information"""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    return StockResponse(
        symbol=stock.symbol,
        name=stock.name,
        sector=stock.sector or "",
        industry=stock.industry or "",
        market_cap=stock.market_cap or 0,
        currency=stock.currency,
        asset_type=stock.asset_type,
        is_active=stock.is_active,
        created_at=stock.created_at,
        updated_at=stock.updated_at
    )

@app.get("/stocks/{symbol}/historical")
async def get_historical_data(
    symbol: str,
    days: int = Query(default=365, ge=1, le=3650),
    db: Session = Depends(get_db)
):
    """Get historical price data"""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Get historical data
    start_date = datetime.now() - timedelta(days=days)
    historical_data = db.query(HistoricalData).filter(
        HistoricalData.stock_id == stock.id,
        HistoricalData.date >= start_date
    ).order_by(HistoricalData.date.desc()).all()
    
    return [
        HistoricalDataResponse(
            date=data.date,
            open_price=data.open_price,
            high_price=data.high_price,
            low_price=data.low_price,
            close_price=data.close_price,
            volume=data.volume,
            dividend_amount=data.dividend_amount
        ) for data in historical_data
    ]

@app.get("/stocks/{symbol}/metrics")
async def get_financial_metrics(symbol: str, db: Session = Depends(get_db)):
    """Get financial metrics"""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Get latest financial metrics
    metrics = db.query(FinancialMetrics).filter(
        FinancialMetrics.stock_id == stock.id
    ).order_by(FinancialMetrics.date.desc()).first()
    
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No financial metrics found for {symbol}")
    
    return FinancialMetricsResponse(
        date=metrics.date,
        pe_ratio=metrics.pe_ratio,
        pb_ratio=metrics.pb_ratio,
        roe=metrics.roe,
        debt_to_equity=metrics.debt_to_equity,
        dividend_yield=metrics.dividend_yield,
        earnings_per_share=metrics.earnings_per_share
    )

@app.get("/stocks/{symbol}/news")
async def get_stock_news(
    symbol: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get recent news for a stock"""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Get recent news
    news_articles = db.query(NewsArticle).filter(
        NewsArticle.stock_id == stock.id
    ).order_by(NewsArticle.published_at.desc()).limit(limit).all()
    
    return [
        NewsResponse(
            title=article.title,
            content=article.content or "",
            url=article.url,
            source=article.source,
            published_at=article.published_at,
            sentiment_score=article.sentiment_score,
            sentiment_label=article.sentiment_label,
            relevance_score=article.relevance_score
        ) for article in news_articles
    ]

@app.get("/stocks/{symbol}/growth-projection")
async def get_growth_projection(
    symbol: str,
    investment_amount: float = Query(default=10000, ge=100),
    years: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get growth projection for a stock"""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Get historical data for analysis
    historical_data = db.query(HistoricalData).filter(
        HistoricalData.stock_id == stock.id
    ).order_by(HistoricalData.date.desc()).limit(252 * 5).all()  # 5 years of data
    
    if len(historical_data) < 252:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient historical data for {symbol}. Need at least 1 year."
        )
    
    # Calculate historical growth metrics
    from src.services.stock_data_service import HistoricalDataPoint
    historical_data_points = [
        HistoricalDataPoint(
            date=data.date,
            open_price=data.open_price,
            high_price=data.high_price,
            low_price=data.low_price,
            close_price=data.close_price,
            volume=data.volume,
            dividend_amount=data.dividend_amount,
            split_coefficient=data.split_coefficient
        ) for data in reversed(historical_data)
    ]
    
    growth_metrics = stock_data_service.calculate_growth_metrics(symbol, historical_data_points)
    
    # Calculate projections
    historical_cagr = growth_metrics.get('cagr_5y', 0)
    required_cagr = calculate_required_cagr(investment_amount, settings.target_final_amount, years)
    
    # Simple projection based on historical CAGR
    projected_value = calculate_future_value(investment_amount, historical_cagr, years)
    
    # Calculate probability of success (simplified)
    volatility = growth_metrics.get('volatility', 0.2)
    sharpe_ratio = growth_metrics.get('sharpe_ratio', 0)
    
    # Simple probability calculation (this could be much more sophisticated)
    probability_of_success = max(0.1, min(0.9, 0.5 + (sharpe_ratio * 0.1) - (volatility * 0.5)))
    
    return GrowthProjection(
        initial_investment=investment_amount,
        projected_value=projected_value,
        years=years,
        required_cagr=required_cagr,
        projected_cagr=historical_cagr,
        probability_of_success=probability_of_success
    )

@app.get("/stocks")
async def list_stocks(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sector: Optional[str] = Query(default=None),
    asset_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """List all stocks with optional filtering"""
    query = db.query(Stock)
    
    # Apply filters
    if sector:
        query = query.filter(Stock.sector == sector)
    if asset_type:
        query = query.filter(Stock.asset_type == asset_type)
    
    # Apply pagination
    stocks = query.offset(offset).limit(limit).all()
    
    return [
        StockResponse(
            symbol=stock.symbol,
            name=stock.name,
            sector=stock.sector or "",
            industry=stock.industry or "",
            market_cap=stock.market_cap or 0,
            currency=stock.currency,
            asset_type=stock.asset_type,
            is_active=stock.is_active,
            created_at=stock.created_at,
            updated_at=stock.updated_at
        ) for stock in stocks
    ]

@app.post("/stocks/{symbol}/update")
async def update_stock_data(
    symbol: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Update data for an existing stock"""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    # Start background data collection
    background_tasks.add_task(
        collect_stock_data_background,
        symbol,
        stock.name
    )
    
    return {
        "message": f"Data update started for {symbol}",
        "symbol": symbol
    }

@app.get("/screen/high-growth")
async def screen_high_growth_stocks(
    min_cagr: float = Query(default=0.3, ge=0.1, le=1.0),
    max_risk: float = Query(default=0.4, ge=0.1, le=1.0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Screen for high-growth stocks that could achieve the target"""
    
    # This is a simplified screening algorithm
    # In practice, this would be much more sophisticated
    
    stocks = db.query(Stock).filter(Stock.is_active == True).all()
    screening_results = []
    
    for stock in stocks:
        try:
            # Get historical data
            historical_data = db.query(HistoricalData).filter(
                HistoricalData.stock_id == stock.id
            ).order_by(HistoricalData.date.desc()).limit(252 * 5).all()
            
            if len(historical_data) < 252:
                continue
            
            # Calculate metrics
            historical_data_points = [
                HistoricalDataPoint(
                    date=data.date,
                    open_price=data.open_price,
                    high_price=data.high_price,
                    low_price=data.low_price,
                    close_price=data.close_price,
                    volume=data.volume,
                    dividend_amount=data.dividend_amount,
                    split_coefficient=data.split_coefficient
                ) for data in reversed(historical_data)
            ]
            
            growth_metrics = stock_data_service.calculate_growth_metrics(
                stock.symbol, 
                historical_data_points
            )
            
            # Apply screening criteria
            cagr_5y = growth_metrics.get('cagr_5y', 0)
            volatility = growth_metrics.get('volatility', 1.0)
            sharpe_ratio = growth_metrics.get('sharpe_ratio', 0)
            
            if cagr_5y >= min_cagr and volatility <= max_risk and sharpe_ratio > 0.5:
                # Get latest financial metrics
                financial_metrics = db.query(FinancialMetrics).filter(
                    FinancialMetrics.stock_id == stock.id
                ).order_by(FinancialMetrics.date.desc()).first()
                
                # Get news sentiment
                news_summary = await news_service.get_news_summary(stock.symbol)
                
                screening_results.append({
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "sector": stock.sector,
                    "historical_cagr": cagr_5y,
                    "volatility": volatility,
                    "sharpe_ratio": sharpe_ratio,
                    "max_drawdown": growth_metrics.get('max_drawdown', 0),
                    "pe_ratio": financial_metrics.pe_ratio if financial_metrics else None,
                    "news_sentiment": news_summary.get('average_sentiment', 0),
                    "projected_10y_value": calculate_future_value(10000, cagr_5y, 10),
                    "meets_target": calculate_future_value(10000, cagr_5y, 10) >= settings.target_final_amount
                })
                
        except Exception as e:
            logger.error(f"Error screening stock {stock.symbol}: {e}")
            continue
    
    # Sort by projected value
    screening_results.sort(key=lambda x: x['projected_10y_value'], reverse=True)
    
    return screening_results[:limit]

# Background tasks
async def collect_stock_data_background(symbol: str, stock_name: str):
    """Background task to collect stock data"""
    try:
        logger.info(f"Starting background data collection for {symbol}")
        result = await data_collection_agent.collect_data(symbol, stock_name)
        logger.info(f"Background data collection completed for {symbol}: {result['status']}")
    except Exception as e:
        logger.error(f"Background data collection failed for {symbol}: {e}")

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 