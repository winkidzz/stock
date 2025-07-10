#!/usr/bin/env python3
"""
Test script for Yahoo Finance Playwright scraper
"""
import asyncio
import sys
import logging
from src.services.yahoo_scraper import create_yahoo_scraper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scraper():
    """Test the Yahoo Finance scraper"""
    symbol = "AAPL"
    
    try:
        logger.info(f"Testing Yahoo Finance scraper for {symbol}")
        
        scraper = await create_yahoo_scraper("chromium")
        async with scraper:
            # Test stock info
            logger.info("Testing stock info extraction...")
            
            # First, debug what elements are available
            await scraper.debug_page_elements(symbol)
            
            stock_info = await scraper.get_stock_info(symbol)
            
            if stock_info:
                logger.info(f"✅ Stock Info Success:")
                logger.info(f"   Name: {stock_info.name}")
                logger.info(f"   Price: ${stock_info.price}")
                logger.info(f"   Sector: {stock_info.sector}")
                logger.info(f"   Industry: {stock_info.industry}")
                logger.info(f"   Market Cap: ${stock_info.market_cap:,.0f}")
            else:
                logger.error("❌ Failed to get stock info")
                return False
            
            # Test historical data
            logger.info("Testing historical data extraction...")
            historical_data = await scraper.get_historical_data(symbol, "1y")
            
            if historical_data:
                logger.info(f"✅ Historical Data Success: {len(historical_data)} data points")
                if historical_data:
                    latest = historical_data[0]
                    logger.info(f"   Latest Date: {latest.date}")
                    logger.info(f"   Latest Close: ${latest.close_price}")
                    logger.info(f"   Latest Volume: {latest.volume:,}")
            else:
                logger.error("❌ Failed to get historical data")
                return False
        
        logger.info("🎉 All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_scraper())
    sys.exit(0 if success else 1) 