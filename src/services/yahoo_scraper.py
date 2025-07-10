import asyncio
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class ScrapedStockInfo:
    symbol: str
    name: str
    price: float
    sector: str
    industry: str
    market_cap: float
    exchange: str
    currency: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    eps: Optional[float] = None
    volume: Optional[int] = None

@dataclass
class ScrapedHistoricalData:
    date: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    adj_close: float

class YahooFinanceScraper:
    """Scrape Yahoo Finance data using Playwright"""
    
    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        self.headless = headless
        self.browser_type = browser_type
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Initialize browser with enhanced settings"""
        try:
            self.playwright = await async_playwright().start()
            
            # Enhanced browser launch args for better compatibility
            launch_args = [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor",
                "--disable-ipc-flooding-protection",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-background-timer-throttling",
                "--force-color-profile=srgb",
                "--metrics-recording-only",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-first-run",
                "--safebrowsing-disable-auto-update",
                "--disable-web-security",
                "--disable-features=TranslateUI",
                "--disable-domain-reliability"
            ]
            
            # Choose browser type
            if self.browser_type.lower() == "brave":
                # For Brave browser (if installed)
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    executable_path="/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",  # macOS path
                    args=launch_args
                )
            elif self.browser_type.lower() == "chromium":
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=launch_args
                )
            elif self.browser_type.lower() == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            else:
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=launch_args
                )
            
            # Create new page with realistic settings
            self.page = await self.browser.new_page()
            
            # Set realistic user agent and headers
            await self.page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            })
            
            # Set viewport and other properties to mimic real browser
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Override navigator.webdriver property
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            logger.info(f"Browser started: {self.browser_type}")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            # Fallback to basic chromium
            if self.browser_type != "chromium":
                logger.info("Falling back to basic chromium")
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
                self.page = await self.browser.new_page()
    
    async def close(self):
        """Close browser"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def get_stock_info(self, symbol: str) -> Optional[ScrapedStockInfo]:
        """Get basic stock information from Yahoo Finance summary page"""
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}"
            
            # Navigate with increased timeout and better wait strategy
            logger.info(f"Navigating to {url}")
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for the page to stabilize
            await self.page.wait_for_timeout(3000)
            
            # Try multiple selectors to find the stock data
            await self._wait_for_any_selector([
                f'[data-symbol="{symbol}"]',
                '[data-test="qsp-price"]',
                'h1[data-reactid]',
                '.D\\(ib\\).Mt\\(4px\\)',
                'fin-streamer[data-symbol]'
            ], timeout=30000)
            
            # Extract company name with JavaScript helper to filter out unwanted text
            name = await self.page.evaluate(f"""
                () => {{
                    // Try multiple approaches to get the company name
                    let companyName = null;
                    
                    // Method 1: Look for the long company name in h1 elements
                    const h1Elements = Array.from(document.querySelectorAll('h1'));
                    for (let h1 of h1Elements) {{
                        const text = h1.textContent?.trim();
                        if (text && text.length > 10 && !text.includes('Yahoo') && !text.includes('Finance')) {{
                            companyName = text;
                            break;
                        }}
                    }}
                    
                    // Method 2: Look for elements with company-like content
                    if (!companyName) {{
                        const selectors = [
                            '[data-test="YFINANCE_QUOTE_DESCRIPTION"]',
                            'span[title*="{symbol}"]',
                            '[data-test*="quote"] *',
                            '.C\\\\(\\\\$c-fuji-grey-j\\\\)'
                        ];
                        
                        for (let selector of selectors) {{
                            try {{
                                const element = document.querySelector(selector);
                                if (element) {{
                                    const text = element.textContent?.trim();
                                    if (text && text.length > 5 && !text.includes('Yahoo') && !text.includes('Finance')) {{
                                        companyName = text;
                                        break;
                                    }}
                                }}
                            }} catch (e) {{}}
                        }}
                    }}
                    
                    // Method 3: Extract from meta tags or title
                    if (!companyName) {{
                        const metaTitle = document.querySelector('meta[property="og:title"]');
                        if (metaTitle) {{
                            const content = metaTitle.getAttribute('content');
                            if (content && content.includes('{symbol}')) {{
                                companyName = content.replace(/\\s*\\(.*?\\)\\s*/g, '').trim();
                            }}
                        }}
                    }}
                    
                    return companyName || '{symbol} Inc';
                }}
            """)
            
            # Extract current price with validation
            price_text = await self.page.evaluate(f"""
                () => {{
                    // Look for price elements with validation
                    const priceSelectors = [
                        'fin-streamer[data-field="regularMarketPrice"]',
                        '[data-test="qsp-price"]',
                        'fin-streamer[data-test="qsp-price"]',
                        '[data-symbol="{symbol}"] fin-streamer[data-field="regularMarketPrice"]',
                        '.Fw\\\\(b\\\\).Fz\\\\(36px\\\\)'
                    ];
                    
                    let candidates = [];
                    
                    // Collect all potential price candidates
                    for (let selector of priceSelectors) {{
                        try {{
                            const elements = document.querySelectorAll(selector);
                            for (let element of elements) {{
                                const text = element.textContent?.trim();
                                if (text) {{
                                    const numericValue = parseFloat(text.replace(/[,$]/g, ''));
                                    if (!isNaN(numericValue) && numericValue > 10 && numericValue < 10000) {{
                                        candidates.push({{ text, value: numericValue, selector }});
                                    }}
                                }}
                            }}
                        }} catch (e) {{}}
                    }}
                    
                    // Sort by value and return the most reasonable price (typically the largest reasonable value)
                    if (candidates.length > 0) {{
                        candidates.sort((a, b) => b.value - a.value);
                        console.log('Price candidates:', candidates);
                        return candidates[0].text;
                    }}
                    
                    // Fallback: look for large price-like numbers in prominent locations
                    const prominentSelectors = [
                        '[class*="price"]',
                        '[class*="Fw(b)"]',
                        '[class*="Fz(36"]',
                        'span[class*="Fw(b)"]'
                    ];
                    
                    for (let selector of prominentSelectors) {{
                        try {{
                            const elements = document.querySelectorAll(selector);
                            for (let element of elements) {{
                                const text = element.textContent?.trim();
                                if (text && /^\\$?[0-9,]+\\.?[0-9]*$/.test(text)) {{
                                    const numericValue = parseFloat(text.replace(/[,$]/g, ''));
                                    if (numericValue > 50 && numericValue < 10000) {{
                                        return text;
                                    }}
                                }}
                            }}
                        }} catch (e) {{}}
                    }}
                    
                    return null;
                }}
            """)
            price = self._parse_number(price_text) if price_text else 0.0
            
            logger.info(f"Extracted - Name: {name}, Price: {price_text} -> {price}")
            
            # Extract market cap and other key statistics
            stats_data = await self._extract_key_statistics_enhanced()
            
            # Get sector/industry with fallback
            sector, industry = await self._extract_sector_industry_enhanced(symbol)
            
            return ScrapedStockInfo(
                symbol=symbol.upper(),
                name=name or f"{symbol} Inc",
                price=price or 0.0,
                sector=sector or "Unknown",
                industry=industry or "Unknown", 
                market_cap=stats_data.get("market_cap", 0.0),
                exchange="Unknown",  # Could extract this if needed
                currency="USD",
                pe_ratio=stats_data.get("pe_ratio"),
                pb_ratio=stats_data.get("pb_ratio"),
                dividend_yield=stats_data.get("dividend_yield"),
                beta=stats_data.get("beta"),
                eps=stats_data.get("eps"),
                volume=stats_data.get("volume")
            )
            
        except Exception as e:
            logger.error(f"Error scraping stock info for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, period: str = "2y") -> List[ScrapedHistoricalData]:
        """Get historical data from Yahoo Finance historical data page"""
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}/history"
            logger.info(f"Navigating to historical data: {url}")
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for page to stabilize
            await self.page.wait_for_timeout(3000)
            
            # Click on period selector if needed
            if period != "1mo":
                await self._select_time_period(period)
            
            # Wait for table to load with multiple selectors
            table_found = await self._wait_for_any_selector([
                'table[data-test="historical-prices"]',
                'table.W\\(100\\%\\)',
                'table[role="table"]',
                'div[data-test="historical-prices"] table',
                'tbody tr'
            ], timeout=20000)
            
            if not table_found:
                logger.error("Historical data table not found")
                return []
            
            # Extract table data with enhanced JavaScript
            table_data = await self.page.evaluate("""
                () => {
                    // Try multiple table selectors (escape CSS properly)
                    let table = document.querySelector('table[data-test="historical-prices"]') ||
                               document.querySelector('table[data-test*="historical"]') ||
                               document.querySelector('table[role="table"]') ||
                               document.querySelectorAll('table')[0] ||
                               (document.querySelector('tbody') && document.querySelector('tbody').closest('table'));
                    
                    if (!table) {
                        console.log('No table found');
                        return [];
                    }
                    
                    const rows = Array.from(table.querySelectorAll('tbody tr'));
                    console.log('Found', rows.length, 'rows');
                    
                    return rows.slice(0, 100).map((row, index) => {  // Limit to first 100 rows
                        const cells = Array.from(row.querySelectorAll('td, th'));
                        if (cells.length < 6) return null;
                        
                        const rowData = {
                            date: cells[0]?.textContent?.trim(),
                            open: cells[1]?.textContent?.trim(),
                            high: cells[2]?.textContent?.trim(), 
                            low: cells[3]?.textContent?.trim(),
                            close: cells[4]?.textContent?.trim(),
                            adjClose: cells[5]?.textContent?.trim(),
                            volume: cells[6]?.textContent?.trim()
                        };
                        
                        console.log('Row', index, ':', rowData);
                        return rowData;
                    }).filter(row => row && row.date && 
                             !row.date.includes('Dividend') && 
                             !row.date.includes('Date') &&
                             row.date.length > 5);
                }
            """)
            
            # Parse the data
            historical_data = []
            for i, row in enumerate(table_data):
                try:
                    # Try multiple date formats
                    date_str = row['date']
                    date = None
                    
                    for date_format in ['%b %d, %Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            date = datetime.strptime(date_str, date_format)
                            break
                        except:
                            continue
                    
                    if not date:
                        logger.warning(f"Could not parse date: {date_str}")
                        continue
                    
                    historical_data.append(ScrapedHistoricalData(
                        date=date,
                        open_price=self._parse_number(row['open']),
                        high_price=self._parse_number(row['high']),
                        low_price=self._parse_number(row['low']),
                        close_price=self._parse_number(row['close']),
                        volume=self._parse_volume(row['volume']),
                        adj_close=self._parse_number(row['adjClose'])
                    ))
                    
                    # Log first few entries for debugging
                    if i < 3:
                        logger.info(f"Parsed row {i}: {date} - Close: {row['close']}")
                        
                except Exception as e:
                    logger.warning(f"Failed to parse row {i}: {row}, error: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(historical_data)} historical data points for {symbol}")
            return historical_data
            
        except Exception as e:
            logger.error(f"Error scraping historical data for {symbol}: {e}")
            return []
    
    async def _wait_for_any_selector(self, selectors: List[str], timeout: int = 30000) -> bool:
        """Wait for any of the given selectors to appear"""
        try:
            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=timeout // len(selectors))
                    logger.info(f"Found element with selector: {selector}")
                    return True
                except:
                    continue
            return False
        except Exception as e:
            logger.warning(f"None of the selectors found: {e}")
            return False
    
    async def _extract_text(self, selector: str) -> Optional[str]:
        """Extract text from element"""
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else None
        except:
            pass
        return None
    
    async def _extract_text_with_fallbacks(self, selectors: List[str]) -> Optional[str]:
        """Try multiple selectors to extract text"""
        for selector in selectors:
            try:
                text = await self._extract_text(selector)
                if text and text.strip():
                    logger.info(f"Found text '{text}' with selector: {selector}")
                    return text.strip()
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        logger.warning(f"All selectors failed: {selectors}")
        return None
    
    async def _extract_key_statistics(self) -> Dict[str, float]:
        """Extract key statistics from the page"""
        try:
            # Navigate to statistics page or extract from current page
            stats = {}
            
            # Try to extract from summary page first
            pe_text = await self._extract_text('[data-test="PE_RATIO-value"]')
            if pe_text:
                stats['pe_ratio'] = self._parse_number(pe_text)
            
            # Extract market cap
            market_cap_text = await self._extract_text('[data-test="MARKET_CAP-value"]')
            if market_cap_text:
                stats['market_cap'] = self._parse_market_cap(market_cap_text)
            
            # Extract volume
            volume_text = await self._extract_text('[data-test="TD_VOLUME-value"]')
            if volume_text:
                stats['volume'] = self._parse_volume(volume_text)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error extracting statistics: {e}")
            return {}
    
    async def _extract_key_statistics_enhanced(self) -> Dict[str, float]:
        """Enhanced key statistics extraction with multiple fallbacks"""
        stats = {}
        
        try:
            # Market Cap with multiple selectors
            market_cap_text = await self._extract_text_with_fallbacks([
                '[data-test="MARKET_CAP-value"]',
                'td[data-test="MARKET_CAP-value"]',
                'fin-streamer[data-field="marketCap"]',
                'span[data-reactid*="marketCap"]',
                'td:contains("Market Cap") + td',
                '[title*="Market Cap"] + *'
            ])
            if market_cap_text:
                stats['market_cap'] = self._parse_market_cap(market_cap_text)
                logger.info(f"Market cap extracted: {market_cap_text} -> {stats['market_cap']}")
            
            # PE Ratio
            pe_text = await self._extract_text_with_fallbacks([
                '[data-test="PE_RATIO-value"]',
                'td[data-test="PE_RATIO-value"]', 
                'fin-streamer[data-field="trailingPE"]',
                'span[data-reactid*="pe"]'
            ])
            if pe_text:
                stats['pe_ratio'] = self._parse_number(pe_text)
            
            # Volume
            volume_text = await self._extract_text_with_fallbacks([
                '[data-test="TD_VOLUME-value"]',
                'fin-streamer[data-field="regularMarketVolume"]',
                'td[data-test="TD_VOLUME-value"]',
                'span[data-reactid*="volume"]'
            ])
            if volume_text:
                stats['volume'] = self._parse_volume(volume_text)
            
            # Beta
            beta_text = await self._extract_text_with_fallbacks([
                '[data-test="BETA_5Y-value"]',
                'td[data-test="BETA_5Y-value"]',
                'fin-streamer[data-field="beta"]'
            ])
            if beta_text:
                stats['beta'] = self._parse_number(beta_text)
            
            # EPS
            eps_text = await self._extract_text_with_fallbacks([
                '[data-test="EPS_RATIO-value"]',
                'td[data-test="EPS_RATIO-value"]',
                'fin-streamer[data-field="epsTrailingTwelveMonths"]'
            ])
            if eps_text:
                stats['eps'] = self._parse_number(eps_text)
            
            logger.info(f"Enhanced stats extracted: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error extracting enhanced statistics: {e}")
            return stats
    
    async def _extract_sector_industry(self, symbol: str) -> Tuple[str, str]:
        """Extract sector and industry from profile page"""
        try:
            profile_url = f"https://finance.yahoo.com/quote/{symbol}/profile"
            await self.page.goto(profile_url, wait_until="networkidle")
            
            # Look for sector and industry information
            sector_element = await self.page.query_selector('[data-test="SECTOR"]')
            industry_element = await self.page.query_selector('[data-test="INDUSTRY"]')
            
            sector = await sector_element.text_content() if sector_element else "Unknown"
            industry = await industry_element.text_content() if industry_element else "Unknown"
            
            return sector, industry
            
        except Exception as e:
            logger.error(f"Error extracting sector/industry: {e}")
            return "Unknown", "Unknown"
    
    async def _extract_sector_industry_enhanced(self, symbol: str) -> Tuple[str, str]:
        """Enhanced sector and industry extraction with multiple strategies"""
        try:
            # Strategy 1: Try to extract from current page first (summary page)
            sector = await self._extract_text_with_fallbacks([
                '[data-test="SECTOR"]',
                'span[data-test="SECTOR"]',
                'a[title*="sector"]',
                'span[title*="Sector"]',
                '.Mt\\(4px\\) .C\\(\\$linkColor\\)'
            ])
            
            industry = await self._extract_text_with_fallbacks([
                '[data-test="INDUSTRY"]', 
                'span[data-test="INDUSTRY"]',
                'a[title*="industry"]',
                'span[title*="Industry"]'
            ])
            
            # If we found both on current page, return them
            if sector and sector != "Unknown" and industry and industry != "Unknown":
                logger.info(f"Sector/Industry found on summary page: {sector}, {industry}")
                return sector, industry
            
            # Strategy 2: Try profile page with shorter timeout
            logger.info("Trying profile page for sector/industry...")
            profile_url = f"https://finance.yahoo.com/quote/{symbol}/profile"
            await self.page.goto(profile_url, wait_until="domcontentloaded", timeout=20000)
            await self.page.wait_for_timeout(2000)
            
            if not sector or sector == "Unknown":
                sector = await self._extract_text_with_fallbacks([
                    '[data-test="SECTOR"]',
                    'span[data-test="SECTOR"]', 
                    'p[data-test="SECTOR"]',
                    'span:contains("Sector") + span',
                    'p:contains("Sector") + p'
                ])
            
            if not industry or industry == "Unknown":
                industry = await self._extract_text_with_fallbacks([
                    '[data-test="INDUSTRY"]',
                    'span[data-test="INDUSTRY"]',
                    'p[data-test="INDUSTRY"]', 
                    'span:contains("Industry") + span',
                    'p:contains("Industry") + p'
                ])
            
            sector = sector or "Unknown"
            industry = industry or "Unknown"
            
            logger.info(f"Final sector/industry: {sector}, {industry}")
            return sector, industry
            
        except Exception as e:
            logger.error(f"Error extracting enhanced sector/industry: {e}")
            return "Unknown", "Unknown"
    
    async def _select_time_period(self, period: str):
        """Select time period for historical data"""
        try:
            # Map period to Yahoo Finance options
            period_map = {
                "1y": "1Y",
                "2y": "2Y", 
                "5y": "5Y",
                "10y": "10Y",
                "max": "MAX"
            }
            
            yahoo_period = period_map.get(period, "2Y")
            
            # Click time period button
            period_selector = await self.page.query_selector(f'button[data-value="{yahoo_period}"]')
            if period_selector:
                await period_selector.click()
                await self.page.wait_for_timeout(2000)  # Wait for data to reload
                
        except Exception as e:
            logger.error(f"Error selecting time period: {e}")
    
    def _parse_number(self, text: str) -> float:
        """Parse number from text, handling commas and formatting"""
        if not text or text == "-":
            return 0.0
        
        try:
            # Remove commas and other formatting
            cleaned = re.sub(r'[^\d.-]', '', text.replace(',', ''))
            return float(cleaned)
        except:
            return 0.0
    
    def _parse_volume(self, text: str) -> int:
        """Parse volume with K, M, B suffixes"""
        if not text or text == "-":
            return 0
        
        try:
            text = text.upper().replace(',', '')
            multiplier = 1
            
            if 'K' in text:
                multiplier = 1000
                text = text.replace('K', '')
            elif 'M' in text:
                multiplier = 1000000
                text = text.replace('M', '')
            elif 'B' in text:
                multiplier = 1000000000
                text = text.replace('B', '')
            
            number = float(re.sub(r'[^\d.-]', '', text))
            return int(number * multiplier)
            
        except:
            return 0
    
    def _parse_market_cap(self, text: str) -> float:
        """Parse market cap with T, B, M suffixes"""
        if not text or text == "-":
            return 0.0
        
        try:
            text = text.upper().replace(',', '')
            multiplier = 1
            
            if 'T' in text:
                multiplier = 1000000000000
                text = text.replace('T', '')
            elif 'B' in text:
                multiplier = 1000000000
                text = text.replace('B', '')
            elif 'M' in text:
                multiplier = 1000000
                text = text.replace('M', '')
            
            number = float(re.sub(r'[^\d.-]', '', text))
            return number * multiplier
            
        except:
            return 0.0
    
    async def debug_page_elements(self, symbol: str):
        """Debug helper to see what elements are available on the page"""
        try:
            # Get page title
            title = await self.page.title()
            logger.info(f"Page title: {title}")
            
            # Check for common elements
            elements_to_check = [
                'h1',
                '[data-test="qsp-price"]', 
                'fin-streamer',
                '[data-test="MARKET_CAP-value"]',
                '[data-test="SECTOR"]',
                'table',
                '.Fw\\(b\\)'
            ]
            
            for selector in elements_to_check:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    first_text = await elements[0].text_content() if elements else "No text"
                    logger.info(f"Found {len(elements)} elements for '{selector}': '{first_text[:50]}'")
                else:
                    logger.info(f"No elements found for '{selector}'")
            
            # Get all fin-streamer elements with their data attributes
            fin_streamers = await self.page.evaluate("""
                () => {
                    const elements = Array.from(document.querySelectorAll('fin-streamer'));
                    return elements.slice(0, 10).map(el => ({
                        text: el.textContent?.trim(),
                        dataField: el.getAttribute('data-field'),
                        dataTest: el.getAttribute('data-test'),
                        dataSymbol: el.getAttribute('data-symbol')
                    })).filter(item => item.text && item.text.length > 0);
                }
            """)
            
            logger.info(f"Found fin-streamers: {fin_streamers}")
            
        except Exception as e:
            logger.error(f"Debug failed: {e}")

# Async factory function
async def create_yahoo_scraper(browser_type: str = "chromium") -> YahooFinanceScraper:
    """Create and initialize a Yahoo Finance scraper"""
    scraper = YahooFinanceScraper(browser_type=browser_type)
    await scraper.start()
    return scraper 