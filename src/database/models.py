from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

Base = declarative_base()

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(Float)
    exchange = Column(String(50))
    currency = Column(String(3), default="USD")
    asset_type = Column(String(20))  # stock, etf, index_fund
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    historical_data = relationship("HistoricalData", back_populates="stock")
    financial_metrics = relationship("FinancialMetrics", back_populates="stock")
    news_articles = relationship("NewsArticle", back_populates="stock")
    screening_results = relationship("ScreeningResult", back_populates="stock")

class HistoricalData(Base):
    __tablename__ = "historical_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    dividend_amount = Column(Float, default=0.0)
    split_coefficient = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="historical_data")
    
    # Indexes
    __table_args__ = (
        Index("idx_stock_date", "stock_id", "date"),
        Index("idx_date", "date"),
    )

class FinancialMetrics(Base):
    __tablename__ = "financial_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Valuation Metrics
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    ps_ratio = Column(Float)
    ev_to_ebitda = Column(Float)
    
    # Profitability Metrics
    roe = Column(Float)
    roa = Column(Float)
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    net_margin = Column(Float)
    
    # Growth Metrics
    revenue_growth_yoy = Column(Float)
    earnings_growth_yoy = Column(Float)
    eps_growth_yoy = Column(Float)
    
    # Financial Health
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    
    # Dividend Metrics
    dividend_yield = Column(Float)
    dividend_payout_ratio = Column(Float)
    
    # Other Metrics
    beta = Column(Float)
    book_value_per_share = Column(Float)
    earnings_per_share = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="financial_metrics")
    
    # Indexes
    __table_args__ = (
        Index("idx_stock_metrics_date", "stock_id", "date"),
    )

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String(1000))
    source = Column(String(100))
    published_at = Column(DateTime, nullable=False)
    sentiment_score = Column(Float)  # -1 to 1 scale
    sentiment_label = Column(String(20))  # positive, negative, neutral
    relevance_score = Column(Float)  # 0 to 1 scale
    
    # Vector embedding for semantic search
    embedding = Column(Vector(384))  # sentence-transformers all-MiniLM-L6-v2 dimension
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="news_articles")
    
    # Indexes
    __table_args__ = (
        Index("idx_stock_news_date", "stock_id", "published_at"),
        Index("idx_news_sentiment", "sentiment_score"),
    )

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    criteria = Column(Text)  # JSON string of screening criteria
    risk_level = Column(String(20))  # low, medium, high
    expected_cagr = Column(Float)
    max_drawdown = Column(Float)
    investment_horizon = Column(Integer)  # years
    
    # AI-generated explanation
    explanation = Column(Text)
    reasoning = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    screening_results = relationship("ScreeningResult", back_populates="strategy")

class ScreeningResult(Base):
    __tablename__ = "screening_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    
    # Scoring
    growth_score = Column(Float)
    value_score = Column(Float)
    quality_score = Column(Float)
    momentum_score = Column(Float)
    overall_score = Column(Float)
    
    # Projections
    projected_cagr = Column(Float)
    projected_value_10y = Column(Float)
    risk_score = Column(Float)
    confidence_level = Column(Float)
    
    # AI Analysis
    analysis_summary = Column(Text)
    key_strengths = Column(ARRAY(String))
    key_risks = Column(ARRAY(String))
    recommendation = Column(String(20))  # buy, hold, sell
    
    screening_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="screening_results")
    strategy = relationship("Strategy", back_populates="screening_results")
    
    # Indexes
    __table_args__ = (
        Index("idx_screening_score", "overall_score"),
        Index("idx_screening_date", "screening_date"),
    ) 