import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
import asyncio
import aiohttp
import time
import random
from sqlalchemy.orm import Session

from ..database import Stock, HistoricalData, FinancialMetrics, get_db_session
from ..config import settings
from .yahoo_scraper import create_yahoo_scraper, ScrapedStockInfo, ScrapedHistoricalData

logger = logging.getLogger(__name__)

@dataclass
class StockInfo:
    symbol: str
    name: str
    sector: str
    industry: str
    market_cap: float
    exchange: str
    currency: str
    asset_type: str

@dataclass
class HistoricalDataPoint:
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    dividend_amount: float
    split_coefficient: float

@dataclass
class FinancialMetricsData:
    date: datetime
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    earnings_growth_yoy: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    dividend_payout_ratio: Optional[float] = None
    beta: Optional[float] = None
    book_value_per_share: Optional[float] = None
    earnings_per_share: Optional[float] = None

def retry_on_rate_limit(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator to retry function calls on rate limit errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    if "429" in error_msg or "too many requests" in error_msg:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(f"Rate limited, retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            continue
                    # Re-raise if it's not a rate limit error or we've exhausted retries
                    raise e
            return None
        return wrapper
    return decorator

class StockDataService:
    def __init__(self):
        self.session = None
        self.use_scraper_fallback = True  # Enable Playwright fallback
        
    @retry_on_rate_limit(max_retries=3, base_delay=2.0)
    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """Get basic stock information with Playwright fallback"""
        try:
            # Add small delay to avoid overwhelming API
            time.sleep(random.uniform(0.1, 0.5))
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Determine asset type
            asset_type = "stock"
            if "ETF" in info.get("longName", "").upper():
                asset_type = "etf"
            elif "INDEX" in info.get("longName", "").upper():
                asset_type = "index_fund"
            
            return StockInfo(
                symbol=symbol.upper(),
                name=info.get("longName", ""),
                sector=info.get("sector", ""),
                industry=info.get("industry", ""),
                market_cap=info.get("marketCap", 0),
                exchange=info.get("exchange", ""),
                currency=info.get("currency", "USD"),
                asset_type=asset_type
            )
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            
            # Try Playwright fallback if enabled
            if self.use_scraper_fallback:
                logger.info(f"Trying Playwright fallback for {symbol}")
                # Create new event loop for scraper to avoid nesting issue
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_stock_info_with_scraper(symbol))
                    return future.result()
            
            return None
    
    @retry_on_rate_limit(max_retries=3, base_delay=2.0)
    def get_historical_data(self, symbol: str, years: int = 10) -> List[HistoricalDataPoint]:
        """Get historical stock data with Playwright fallback"""
        try:
            # Add small delay to avoid overwhelming API
            time.sleep(random.uniform(0.1, 0.5))
            
            ticker = yf.Ticker(symbol)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            # Fetch data
            hist = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            
            historical_data = []
            for index, row in hist.iterrows():
                historical_data.append(HistoricalDataPoint(
                    date=index.to_pydatetime(),
                    open_price=float(row['Open']),
                    high_price=float(row['High']),
                    low_price=float(row['Low']),
                    close_price=float(row['Close']),
                    volume=int(row['Volume']),
                    dividend_amount=float(row.get('Dividends', 0)),
                    split_coefficient=float(row.get('Stock Splits', 1))
                ))
            
            return historical_data
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            
            # Try Playwright fallback if enabled
            if self.use_scraper_fallback:
                logger.info(f"Trying Playwright fallback for historical data: {symbol}")
                # Create new event loop for scraper to avoid nesting issue
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_historical_data_with_scraper(symbol, years))
                    return future.result()
            
            return []
    
    @retry_on_rate_limit(max_retries=3, base_delay=2.0)
    def get_financial_metrics(self, symbol: str) -> Optional[FinancialMetricsData]:
        """Get current financial metrics"""
        try:
            # Add small delay to avoid overwhelming API
            time.sleep(random.uniform(0.1, 0.5))
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return FinancialMetricsData(
                date=datetime.now(),
                pe_ratio=info.get("trailingPE"),
                pb_ratio=info.get("priceToBook"),
                ps_ratio=info.get("priceToSalesTrailing12Months"),
                ev_to_ebitda=info.get("enterpriseToEbitda"),
                roe=info.get("returnOnEquity"),
                roa=info.get("returnOnAssets"),
                gross_margin=info.get("grossMargins"),
                operating_margin=info.get("operatingMargins"),
                net_margin=info.get("profitMargins"),
                revenue_growth_yoy=info.get("revenueGrowth"),
                earnings_growth_yoy=info.get("earningsGrowth"),
                debt_to_equity=info.get("debtToEquity"),
                current_ratio=info.get("currentRatio"),
                quick_ratio=info.get("quickRatio"),
                dividend_yield=info.get("dividendYield"),
                dividend_payout_ratio=info.get("payoutRatio"),
                beta=info.get("beta"),
                book_value_per_share=info.get("bookValue"),
                earnings_per_share=info.get("trailingEps")
            )
        except Exception as e:
            logger.error(f"Error fetching financial metrics for {symbol}: {e}")
            return None
    
    def calculate_growth_metrics(self, symbol: str, historical_data: List[HistoricalDataPoint]) -> Dict[str, float]:
        """Calculate growth metrics from historical data"""
        if len(historical_data) < 252:  # Need at least 1 year of data
            return {}
        
        try:
            # Convert to DataFrame for easier calculation
            df = pd.DataFrame([
                {
                    'date': point.date,
                    'close': point.close_price,
                    'volume': point.volume
                } for point in historical_data
            ])
            df = df.sort_values('date')
            
            # Calculate various growth metrics
            current_price = df['close'].iloc[-1]
            price_1y_ago = df['close'].iloc[-252] if len(df) >= 252 else df['close'].iloc[0]
            price_5y_ago = df['close'].iloc[-1260] if len(df) >= 1260 else df['close'].iloc[0]
            
            # Calculate CAGR
            cagr_1y = (current_price / price_1y_ago) - 1
            cagr_5y = ((current_price / price_5y_ago) ** (1/5)) - 1 if len(df) >= 1260 else 0
            
            # Calculate volatility (standard deviation of returns)
            df['returns'] = df['close'].pct_change()
            volatility = df['returns'].std() * np.sqrt(252)  # Annualized volatility
            
            # Calculate maximum drawdown
            df['peak'] = df['close'].cummax()
            df['drawdown'] = (df['close'] - df['peak']) / df['peak']
            max_drawdown = df['drawdown'].min()
            
            # Calculate Sharpe ratio (assuming 3% risk-free rate)
            risk_free_rate = 0.03
            avg_return = df['returns'].mean() * 252
            sharpe_ratio = (avg_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            return {
                'cagr_1y': cagr_1y,
                'cagr_5y': cagr_5y,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'current_price': current_price
            }
        except Exception as e:
            logger.error(f"Error calculating growth metrics for {symbol}: {e}")
            return {}
    
    def save_stock_data(self, symbol: str, stock_name: str = None) -> bool:
        """Save complete stock data to database"""
        try:
            with get_db_session() as db:
                # Get or create stock
                stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
                
                if not stock:
                    # Try to get stock info
                    stock_info = self.get_stock_info(symbol)
                    
                    if stock_info:
                        # Create new stock record with full data
                        stock = Stock(
                            symbol=stock_info.symbol,
                            name=stock_info.name,
                            sector=stock_info.sector,
                            industry=stock_info.industry,
                            market_cap=stock_info.market_cap,
                            exchange=stock_info.exchange,
                            currency=stock_info.currency,
                            asset_type=stock_info.asset_type
                        )
                    else:
                        # Create basic stock record if API fails
                        logger.warning(f"Unable to fetch full stock info for {symbol}, creating basic record")
                        stock = Stock(
                            symbol=symbol.upper(),
                            name=stock_name or symbol.upper(),
                            sector="Unknown",
                            industry="Unknown",
                            market_cap=0,
                            exchange="Unknown",
                            currency="USD",
                            asset_type="stock"
                        )
                    
                    db.add(stock)
                    db.flush()  # Get the ID
                
                # Get historical data
                historical_data = self.get_historical_data(symbol, settings.historical_data_years)
                
                # Save historical data
                for data_point in historical_data:
                    # Check if data point already exists
                    existing = db.query(HistoricalData).filter(
                        HistoricalData.stock_id == stock.id,
                        HistoricalData.date == data_point.date
                    ).first()
                    
                    if not existing:
                        hist_data = HistoricalData(
                            stock_id=stock.id,
                            date=data_point.date,
                            open_price=data_point.open_price,
                            high_price=data_point.high_price,
                            low_price=data_point.low_price,
                            close_price=data_point.close_price,
                            volume=data_point.volume,
                            dividend_amount=data_point.dividend_amount,
                            split_coefficient=data_point.split_coefficient
                        )
                        db.add(hist_data)
                
                # Get and save financial metrics
                financial_metrics = self.get_financial_metrics(symbol)
                if financial_metrics:
                    # Check if metrics already exist for today
                    today = datetime.now().date()
                    existing_metrics = db.query(FinancialMetrics).filter(
                        FinancialMetrics.stock_id == stock.id,
                        FinancialMetrics.date >= today
                    ).first()
                    
                    if not existing_metrics:
                        metrics = FinancialMetrics(
                            stock_id=stock.id,
                            date=financial_metrics.date,
                            pe_ratio=financial_metrics.pe_ratio,
                            pb_ratio=financial_metrics.pb_ratio,
                            ps_ratio=financial_metrics.ps_ratio,
                            ev_to_ebitda=financial_metrics.ev_to_ebitda,
                            roe=financial_metrics.roe,
                            roa=financial_metrics.roa,
                            gross_margin=financial_metrics.gross_margin,
                            operating_margin=financial_metrics.operating_margin,
                            net_margin=financial_metrics.net_margin,
                            revenue_growth_yoy=financial_metrics.revenue_growth_yoy,
                            earnings_growth_yoy=financial_metrics.earnings_growth_yoy,
                            debt_to_equity=financial_metrics.debt_to_equity,
                            current_ratio=financial_metrics.current_ratio,
                            quick_ratio=financial_metrics.quick_ratio,
                            dividend_yield=financial_metrics.dividend_yield,
                            dividend_payout_ratio=financial_metrics.dividend_payout_ratio,
                            beta=financial_metrics.beta,
                            book_value_per_share=financial_metrics.book_value_per_share,
                            earnings_per_share=financial_metrics.earnings_per_share
                        )
                        db.add(metrics)
                
                db.commit()
                logger.info(f"Successfully saved data for {symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving stock data for {symbol}: {e}")
            return False
    
    async def update_multiple_stocks(self, symbols: List[str]) -> Dict[str, bool]:
        """Update multiple stocks concurrently"""
        results = {}
        
        # Create tasks for concurrent execution
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._update_stock_async(symbol))
            tasks.append((symbol, task))
        
        # Wait for all tasks to complete
        for symbol, task in tasks:
            try:
                result = await task
                results[symbol] = result
            except Exception as e:
                logger.error(f"Error updating {symbol}: {e}")
                results[symbol] = False
        
        return results
    
    async def _update_stock_async(self, symbol: str) -> bool:
        """Async wrapper for stock update"""
        return await asyncio.to_thread(self.save_stock_data, symbol)
    
    async def _get_stock_info_with_scraper(self, symbol: str) -> Optional[StockInfo]:
        """Get stock info using Playwright scraper"""
        try:
            scraper = await create_yahoo_scraper("chromium")
            async with scraper:
                scraped_info = await scraper.get_stock_info(symbol)
                
                if scraped_info:
                    # Convert ScrapedStockInfo to StockInfo
                    return StockInfo(
                        symbol=scraped_info.symbol,
                        name=scraped_info.name,
                        sector=scraped_info.sector,
                        industry=scraped_info.industry,
                        market_cap=scraped_info.market_cap,
                        exchange=scraped_info.exchange,
                        currency=scraped_info.currency,
                        asset_type="stock"  # Default to stock
                    )
        except Exception as e:
            logger.error(f"Error scraping stock info for {symbol}: {e}")
        
        return None
    
    async def _get_historical_data_with_scraper(self, symbol: str, years: int = 10) -> List[HistoricalDataPoint]:
        """Get historical data using Playwright scraper"""
        try:
            # Map years to period for scraper
            if years <= 1:
                period = "1y"
            elif years <= 2:
                period = "2y"
            elif years <= 5:
                period = "5y"
            else:
                period = "10y"
            
            scraper = await create_yahoo_scraper("chromium")
            async with scraper:
                scraped_data = await scraper.get_historical_data(symbol, period)
                
                # Convert ScrapedHistoricalData to HistoricalDataPoint
                historical_data = []
                for data in scraped_data:
                    historical_data.append(HistoricalDataPoint(
                        date=data.date,
                        open_price=data.open_price,
                        high_price=data.high_price,
                        low_price=data.low_price,
                        close_price=data.close_price,
                        volume=data.volume,
                        dividend_amount=0.0,  # Not scraped yet
                        split_coefficient=1.0  # Not scraped yet
                    ))
                
                logger.info(f"Scraped {len(historical_data)} data points for {symbol}")
                return historical_data
                
        except Exception as e:
            logger.error(f"Error scraping historical data for {symbol}: {e}")
        
        return []

# Create global instance
stock_data_service = StockDataService() 