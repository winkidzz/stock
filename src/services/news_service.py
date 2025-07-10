import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session
import numpy as np

from langchain_ollama import OllamaLLM
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate

from ..database import Stock, NewsArticle, get_db_session
from ..config import settings

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Embeddings will be disabled.")

@dataclass
class NewsItem:
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    relevance_score: float = 0.0

@dataclass
class SentimentAnalysis:
    score: float  # -1 to 1
    label: str   # positive, negative, neutral
    confidence: float

class NewsService:
    def __init__(self):
        self.brave_api_key = settings.brave_api_key
        self.base_url = "https://api.search.brave.com/res/v1/news"
        
        # Initialize local LLM
        self.llm = OllamaLLM(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature
        )
        
        # Fast LLM for quick operations
        self.llm_fast = OllamaLLM(
            model=settings.llm_model_fast,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature
        )
        
        # Initialize local embedding model
        self.embedding_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use a good general-purpose embedding model
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence-transformers embedding model")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
                self.embedding_model = None
        
    async def search_news(self, query: str, count: int = 20) -> List[NewsItem]:
        """Search for news articles using Brave Search API"""
        if not self.brave_api_key:
            logger.warning("Brave API key not provided, skipping news search")
            return []
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.brave_api_key
        }
        
        params = {
            "q": query,
            "count": count,
            "freshness": "1w",  # Last week
            "text_decorations": False,
            "search_lang": "en",
            "country": "US",
            "spellcheck": True,
            "result_filter": "news",
            "safesearch": "moderate"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_news_response(data)
                    else:
                        logger.error(f"Brave API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return []
    
    def _parse_news_response(self, data: Dict) -> List[NewsItem]:
        """Parse Brave Search API response"""
        news_items = []
        
        if "news" not in data or "results" not in data["news"]:
            return news_items
        
        for item in data["news"]["results"]:
            try:
                # Parse published date
                published_at = datetime.fromisoformat(
                    item.get("age", datetime.now().isoformat())
                )
                
                news_item = NewsItem(
                    title=item.get("title", ""),
                    content=item.get("description", ""),
                    url=item.get("url", ""),
                    source=item.get("source", ""),
                    published_at=published_at,
                    relevance_score=self._calculate_relevance_score(item)
                )
                news_items.append(news_item)
            except Exception as e:
                logger.error(f"Error parsing news item: {e}")
                continue
        
        return news_items
    
    def _calculate_relevance_score(self, item: Dict) -> float:
        """Calculate relevance score based on various factors"""
        score = 0.0
        
        # Base score
        score += 0.5
        
        # Recency bonus (more recent = higher score)
        try:
            published_at = datetime.fromisoformat(item.get("age", datetime.now().isoformat()))
            days_old = (datetime.now() - published_at).days
            recency_bonus = max(0, 1 - (days_old / 7))  # Decay over 7 days
            score += recency_bonus * 0.3
        except:
            pass
        
        # Title relevance (simple keyword matching)
        title = item.get("title", "").lower()
        financial_keywords = [
            "earnings", "revenue", "profit", "stock", "shares", "dividend",
            "growth", "analyst", "forecast", "upgrade", "downgrade", "buy",
            "sell", "target", "price", "market", "trading", "volume"
        ]
        
        keyword_matches = sum(1 for keyword in financial_keywords if keyword in title)
        score += (keyword_matches / len(financial_keywords)) * 0.2
        
        return min(1.0, score)
    
    async def analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """Analyze sentiment of news text using local LLM"""
        try:
            # Create sentiment analysis prompt
            prompt = f"""You are a financial sentiment analyst. Analyze the sentiment of the given text and respond with ONLY a JSON object containing:
- score: float between -1.0 (very negative) and 1.0 (very positive)
- label: "positive", "negative", or "neutral"
- confidence: float between 0.0 and 1.0

Focus on financial implications and market sentiment.

Text to analyze: {text}

JSON response:"""
            
            # Use the fast model for sentiment analysis
            response = await asyncio.to_thread(
                self.llm_fast.invoke,
                prompt
            )
            
            # Extract JSON from response
            try:
                # Try to find JSON in the response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]
                    sentiment_data = json.loads(json_str)
                else:
                    # Fallback parsing
                    sentiment_data = json.loads(response.strip())
                
                return SentimentAnalysis(
                    score=float(sentiment_data.get("score", 0.0)),
                    label=sentiment_data.get("label", "neutral"),
                    confidence=float(sentiment_data.get("confidence", 0.0))
                )
            except json.JSONDecodeError:
                # Fallback: parse response manually
                logger.warning(f"Failed to parse JSON from LLM response: {response}")
                return self._parse_sentiment_fallback(response)
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return SentimentAnalysis(score=0.0, label="neutral", confidence=0.0)
    
    def _parse_sentiment_fallback(self, response: str) -> SentimentAnalysis:
        """Fallback sentiment parsing when JSON parsing fails"""
        response_lower = response.lower()
        
        # Simple keyword-based sentiment analysis
        if "positive" in response_lower:
            return SentimentAnalysis(score=0.5, label="positive", confidence=0.6)
        elif "negative" in response_lower:
            return SentimentAnalysis(score=-0.5, label="negative", confidence=0.6)
        else:
            return SentimentAnalysis(score=0.0, label="neutral", confidence=0.5)
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get text embedding using local sentence-transformers model"""
        if not self.embedding_model:
            return None
        
        try:
            # Generate embedding using sentence-transformers
            embedding = await asyncio.to_thread(
                self.embedding_model.encode,
                text,
                convert_to_tensor=False
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    async def collect_stock_news(self, symbol: str, stock_name: str) -> List[NewsItem]:
        """Collect news for a specific stock"""
        queries = [
            f"{symbol} stock",
            f"{stock_name}",
            f"{symbol} earnings",
            f"{stock_name} financial results",
            f"{symbol} analyst rating"
        ]
        
        all_news = []
        for query in queries:
            news_items = await self.search_news(query, count=5)
            all_news.extend(news_items)
        
        # Remove duplicates based on URL
        unique_news = {}
        for item in all_news:
            if item.url not in unique_news:
                unique_news[item.url] = item
        
        # Sort by relevance and recency
        sorted_news = sorted(
            unique_news.values(),
            key=lambda x: (x.relevance_score, x.published_at),
            reverse=True
        )
        
        return sorted_news[:settings.max_news_articles_per_stock]
    
    async def save_news_to_db(self, symbol: str, news_items: List[NewsItem]) -> bool:
        """Save news items to database"""
        try:
            with get_db_session() as db:
                # Get stock
                stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
                if not stock:
                    logger.error(f"Stock {symbol} not found in database")
                    return False
                
                for news_item in news_items:
                    # Check if article already exists
                    existing = db.query(NewsArticle).filter(
                        NewsArticle.url == news_item.url,
                        NewsArticle.stock_id == stock.id
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Analyze sentiment
                    sentiment = await self.analyze_sentiment(
                        f"{news_item.title} {news_item.content}"
                    )
                    
                    # Get embedding
                    embedding = await self.get_embedding(
                        f"{news_item.title} {news_item.content}"
                    )
                    
                    # Create news article
                    article = NewsArticle(
                        stock_id=stock.id,
                        title=news_item.title,
                        content=news_item.content,
                        url=news_item.url,
                        source=news_item.source,
                        published_at=news_item.published_at,
                        sentiment_score=sentiment.score,
                        sentiment_label=sentiment.label,
                        relevance_score=news_item.relevance_score,
                        embedding=embedding
                    )
                    
                    db.add(article)
                
                db.commit()
                logger.info(f"Successfully saved {len(news_items)} news articles for {symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving news to database: {e}")
            return False
    
    async def get_news_summary(self, symbol: str) -> Dict[str, any]:
        """Get news summary for a stock"""
        try:
            with get_db_session() as db:
                stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
                if not stock:
                    return {}
                
                # Get recent news (last 7 days)
                week_ago = datetime.now() - timedelta(days=7)
                recent_news = db.query(NewsArticle).filter(
                    NewsArticle.stock_id == stock.id,
                    NewsArticle.published_at >= week_ago
                ).order_by(NewsArticle.published_at.desc()).all()
                
                if not recent_news:
                    return {
                        "symbol": symbol,
                        "article_count": 0,
                        "average_sentiment": 0.0,
                        "sentiment_trend": "neutral",
                        "top_articles": []
                    }
                
                # Calculate sentiment statistics
                sentiments = [article.sentiment_score for article in recent_news if article.sentiment_score]
                avg_sentiment = np.mean(sentiments) if sentiments else 0.0
                
                # Determine sentiment trend
                if avg_sentiment > 0.2:
                    sentiment_trend = "positive"
                elif avg_sentiment < -0.2:
                    sentiment_trend = "negative"
                else:
                    sentiment_trend = "neutral"
                
                # Get top articles by relevance
                top_articles = sorted(
                    recent_news,
                    key=lambda x: x.relevance_score,
                    reverse=True
                )[:5]
                
                return {
                    "symbol": symbol,
                    "article_count": len(recent_news),
                    "average_sentiment": avg_sentiment,
                    "sentiment_trend": sentiment_trend,
                    "top_articles": [
                        {
                            "title": article.title,
                            "url": article.url,
                            "source": article.source,
                            "published_at": article.published_at.isoformat(),
                            "sentiment_score": article.sentiment_score,
                            "sentiment_label": article.sentiment_label,
                            "relevance_score": article.relevance_score
                        } for article in top_articles
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting news summary for {symbol}: {e}")
            return {}
    
    async def update_stock_news(self, symbol: str, stock_name: str) -> bool:
        """Update news for a specific stock"""
        try:
            # Collect news
            news_items = await self.collect_stock_news(symbol, stock_name)
            
            # Save to database
            success = await self.save_news_to_db(symbol, news_items)
            
            return success
        except Exception as e:
            logger.error(f"Error updating stock news for {symbol}: {e}")
            return False

# Create global instance
news_service = NewsService() 