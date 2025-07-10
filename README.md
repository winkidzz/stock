# Stock Screener: AI-Powered Investment Analysis

## 🎯 Overview

This is a comprehensive stock screener application built with **LangChain**, **LangGraph**, and **FastAPI** that helps identify high-growth investment opportunities. The application aims to find stocks, ETFs, and index funds that could potentially turn $10,000 into $2,000,000 over 10 years (requiring a 34.9% CAGR).

## 🏗️ Architecture

### Technology Stack
- **Backend**: Python 3.11 with FastAPI
- **AI/ML**: LangChain + LangGraph for intelligent workflows
- **Local LLM**: Ollama with Llama 3, Gemma 3, or Mistral
- **Database**: PostgreSQL with pgvector for semantic search
- **Cache**: Redis for performance optimization
- **APIs**: Brave Search, financial data providers
- **Deployment**: Docker & Docker Compose

### Key Features
- **Stock Data Collection**: Historical prices, financial metrics, dividends
- **Real-time News Analysis**: Sentiment analysis using Brave Search + OpenAI
- **AI-Powered Screening**: LangGraph agents for intelligent analysis
- **Vector Search**: Semantic search through news and financial data
- **Growth Projections**: Calculate potential returns and risk metrics
- **Strategy Explanations**: AI-generated investment reasoning

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose OR Python 3.11+
- **Local LLM (Ollama)** - for AI analysis
- API Keys for:
  - Brave Search (for news)
  - Alpha Vantage (optional, for additional financial data)

### Installation

#### Option 1: Local LLM Setup (Recommended)

1. **Install Ollama**
   ```bash
   # Visit https://ollama.ai/ and install for your OS
   # Then start Ollama
   ollama serve
   ```

2. **Install LLM Models**
   ```bash
   # Install recommended models (choose based on your hardware)
   ollama pull llama3:8b          # Fast, efficient (4.7GB)
   ollama pull gemma3:27b         # Balanced quality (17GB)
   ollama pull mistral:latest     # Good alternative (4.1GB)
   ```

3. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd stock-screener
   ```

4. **Auto-setup with Local LLM**
   ```bash
   ./start_with_local_llm.sh
   ```

#### Option 2: Docker Setup (with Host Ollama)

1. **Ensure Ollama is running on host**
   ```bash
   # Make sure Ollama is running on your host machine
   ollama serve
   
   # Verify your models are available
   ollama list
   ```

2. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stock-screener
   ```

3. **Auto-setup with Docker**
   ```bash
   # This will start PostgreSQL, Redis, and the application
   # while connecting to your host Ollama instance
   ./start_with_docker.sh
   ```

4. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Database: localhost:5432 (postgres/postgres)
   - Redis: localhost:6379

5. **Manage the stack**
   ```bash
   ./start_with_docker.sh stop     # Stop all services
   ./start_with_docker.sh logs     # View logs
   ./start_with_docker.sh status   # Check status
   ./start_with_docker.sh clean    # Clean up everything
   ```

## 🏗️ Architecture

### Local Development
- **Python Application**: Runs directly on host
- **Ollama**: Runs on host machine (port 11434)
- **Database**: SQLite or external PostgreSQL

### Docker Production
- **Application Container**: FastAPI + Python services
- **PostgreSQL Container**: Database with pgvector
- **Redis Container**: Caching layer
- **Ollama**: Runs on host machine (connected via `host.docker.internal:11434`)

```
┌─────────────────┐    ┌─────────────────┐
│   Docker Stack │    │   Host Machine  │
│                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │
│  │FastAPI App│──┼────┼──│  Ollama   │  │
│  └───────────┘  │    │  │ (LLMs)    │  │
│  ┌───────────┐  │    │  └───────────┘  │
│  │PostgreSQL │  │    │                 │
│  └───────────┘  │    │                 │
│  ┌───────────┐  │    │                 │
│  │   Redis   │  │    │                 │
│  └───────────┘  │    │                 │
└─────────────────┘    └─────────────────┘
```

## 📊 Investment Goal

**Target**: Transform $10,000 → $2,000,000 in 10 years

- **Required CAGR**: 34.9%
- **Risk Level**: High (aggressive growth strategy)
- **Asset Classes**: Stocks, ETFs, Index Funds, High-dividend stocks

## 🤖 AI Agent Architecture

The application uses LangGraph to orchestrate multiple AI agents:

### 1. Data Collection Agent
- Fetches historical stock data
- Collects financial metrics
- Gathers news articles
- Validates data quality

### 2. News Analysis Agent
- Searches for relevant news using Brave API
- Performs sentiment analysis
- Creates vector embeddings for semantic search
- Tracks market sentiment trends

### 3. Analysis Agent
- Calculates growth metrics (CAGR, volatility, Sharpe ratio)
- Performs risk assessment
- Generates investment scores
- Projects future performance

### 4. Strategy Agent
- Explains investment rationale
- Identifies key strengths and risks
- Provides buy/hold/sell recommendations
- Generates human-readable strategy descriptions

## 📈 Core Metrics & Calculations

### Growth Metrics
- **CAGR (Compound Annual Growth Rate)**: Historical growth rate
- **Volatility**: Standard deviation of returns
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline

### Financial Metrics
- **P/E Ratio**: Price-to-earnings ratio
- **P/B Ratio**: Price-to-book ratio
- **ROE**: Return on equity
- **Debt-to-Equity**: Financial leverage
- **Dividend Yield**: Annual dividend percentage

### Risk Assessment
- **Beta**: Market sensitivity
- **VaR (Value at Risk)**: Potential losses
- **Correlation**: Relationship with market indices

## 🔧 API Endpoints

### Stock Management
- `POST /stocks/add` - Add new stock to database
- `GET /stocks/{symbol}` - Get stock information
- `GET /stocks` - List all stocks with filtering
- `POST /stocks/{symbol}/update` - Update stock data

### Data Retrieval
- `GET /stocks/{symbol}/historical` - Historical price data
- `GET /stocks/{symbol}/metrics` - Financial metrics
- `GET /stocks/{symbol}/news` - Recent news with sentiment
- `GET /stocks/{symbol}/growth-projection` - Growth projections

### Screening
- `GET /screen/high-growth` - Find high-growth stocks
- `GET /screen/dividend` - Find dividend-paying stocks
- `GET /screen/value` - Find undervalued stocks

## 📊 Database Schema

### Core Tables
- **stocks**: Basic stock information
- **historical_data**: Daily price and volume data
- **financial_metrics**: Quarterly financial ratios
- **news_articles**: News with sentiment and embeddings
- **strategies**: Investment strategies and explanations
- **screening_results**: AI analysis results

### Vector Search
- News articles are embedded using OpenAI's text-embedding-ada-002
- Vector similarity search for related content
- Semantic analysis of market sentiment

## 🤖 Local LLM Configuration

### Model Selection Guide

| Model | Size | Best For | RAM Required |
|-------|------|----------|--------------|
| **llama3:8b** | 4.7GB | Fast operations, sentiment analysis | 8GB+ |
| **gemma3:27b** | 17GB | Balanced quality, complex analysis | 32GB+ |
| **mistral:latest** | 4.1GB | Good alternative, instruction following | 8GB+ |
| **deepseek-r1:70b** | 42GB | Highest quality, complex reasoning | 64GB+ |

### Configuration Options

```bash
# Environment variables for local LLM
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=gemma3:27b              # Primary model for analysis
LLM_MODEL_FAST=llama3:8b          # Fast model for quick tasks
LLM_MODEL_ANALYSIS=deepseek-r1:70b # High-quality model (optional)
```

### Model Usage in Application

- **Sentiment Analysis**: Uses `LLM_MODEL_FAST` for speed
- **Investment Explanations**: Uses `LLM_MODEL` for quality
- **Complex Analysis**: Uses `LLM_MODEL_ANALYSIS` if available
- **Embeddings**: Uses sentence-transformers (all-MiniLM-L6-v2)

## 🎯 Example Screening Criteria

### High-Growth Stocks
```python
criteria = {
    "min_cagr": 0.30,           # 30% minimum CAGR
    "max_volatility": 0.40,     # 40% maximum volatility
    "min_sharpe_ratio": 0.5,    # Minimum risk-adjusted return
    "min_market_cap": 1e9,      # $1B+ market cap
    "max_pe_ratio": 30,         # Not overvalued
    "positive_sentiment": True   # Good news sentiment
}
```

### Dividend Growth Stocks
```python
criteria = {
    "min_dividend_yield": 0.02,      # 2% minimum yield
    "dividend_growth_rate": 0.05,    # 5% annual growth
    "payout_ratio": 0.60,           # Sustainable payout
    "consecutive_years": 10          # 10+ years of payments
}
```

## 🚀 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
python -c "from src.database import init_database; init_database()"

# Run the application
uvicorn src.main:app --reload
```

### Testing
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Code Quality
```bash
# Format code
black src/

# Check linting
flake8 src/
```

## 📈 Usage Examples

### Adding a Stock
```bash
curl -X POST "http://localhost:8000/stocks/add" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "name": "Apple Inc."}'
```

### Screening High-Growth Stocks
```bash
curl "http://localhost:8000/screen/high-growth?min_cagr=0.3&max_risk=0.4&limit=10"
```

### Getting Growth Projections
```bash
curl "http://localhost:8000/stocks/AAPL/growth-projection?investment_amount=10000&years=10"
```

## ⚠️ Important Disclaimers

1. **Not Financial Advice**: This application is for educational and research purposes only
2. **High Risk**: 34.9% CAGR target is extremely aggressive and unlikely
3. **Past Performance**: Historical returns don't guarantee future results
4. **Diversification**: Consider portfolio diversification and risk management
5. **Professional Consultation**: Consult with qualified financial advisors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or issues, please create an issue in the GitHub repository.

---

**Remember**: Investing involves risk, including potential loss of principal. Always do your own research and consider your risk tolerance before making investment decisions. 