# 🚀 Quick Start - Docker with Host Ollama

This guide gets you up and running with the stock screener in under 5 minutes using Docker containers with your existing Ollama setup.

## ⚡ Prerequisites

- Docker & Docker Compose installed
- Ollama running on host machine with models

## 🏁 Quick Start

### 1. Verify Ollama is Running
```bash
# Check Ollama is running
ollama serve

# Verify models are available
ollama list
```

You should see your models listed:
```
NAME                  ID              SIZE      MODIFIED
llama3:8b             365c0bd3c000    4.7 GB    8 days ago
gemma3:27b            a418f5838eaf    17 GB     8 weeks ago
mistral:latest        3944fe81ec14    4.1 GB    3 weeks ago
```

### 2. Start the Application
```bash
# Clone and start everything
git clone <repository-url>
cd stock-screener

# Auto-setup and start Docker stack
./start_with_docker.sh
```

### 3. Access the Application
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database**: localhost:5432 (postgres/postgres)

## 🧪 Quick Test

### Test API Connection
```bash
# Health check
curl http://localhost:8000/health

# Add a stock
curl -X POST "http://localhost:8000/stocks/add" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "name": "Apple Inc."}'

# Get stock info
curl http://localhost:8000/stocks/AAPL
```

### Test LLM Integration
```bash
# Test sentiment analysis
curl -X POST "http://localhost:8000/test-sentiment" \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple reports record earnings, stock surges"}'
```

## 🔧 Management Commands

```bash
# View service status
./start_with_docker.sh status

# View logs
./start_with_docker.sh logs

# Stop services
./start_with_docker.sh stop

# Clean up everything
./start_with_docker.sh clean
```

## 📊 Using the Stock Screener

### 1. Add Stocks
```bash
# Add popular stocks
curl -X POST "http://localhost:8000/stocks/add" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "name": "Apple Inc."}'

curl -X POST "http://localhost:8000/stocks/add" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "TSLA", "name": "Tesla Inc."}'

curl -X POST "http://localhost:8000/stocks/add" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NVDA", "name": "NVIDIA Corporation"}'
```

### 2. Get Growth Projections
```bash
# Check if AAPL can turn $10k into $2M in 10 years
curl "http://localhost:8000/stocks/AAPL/growth-projection?investment_amount=10000&years=10"
```

### 3. Screen High-Growth Stocks
```bash
# Find stocks with 30%+ CAGR potential
curl "http://localhost:8000/screen/high-growth?min_cagr=0.30&limit=10"
```

### 4. Get Stock News with Sentiment
```bash
# Get recent news with AI sentiment analysis
curl "http://localhost:8000/stocks/AAPL/news?limit=5"
```

## 🎯 Key Features to Try

1. **Growth Projections**: See if stocks can achieve 34.9% CAGR
2. **Sentiment Analysis**: AI-powered news sentiment using your local LLM
3. **High-Growth Screening**: Find stocks with aggressive growth potential
4. **Risk Assessment**: Volatility, Sharpe ratio, maximum drawdown
5. **Vector Search**: Semantic search through financial news

## 🚨 Troubleshooting

### Ollama Connection Issues
```bash
# Check Ollama is accessible from Docker
docker run --rm curlimages/curl:latest curl -s http://host.docker.internal:11434/api/tags
```

### Container Issues
```bash
# Check all containers are running
docker-compose ps

# View application logs
docker-compose logs app

# Restart specific service
docker-compose restart app
```

### Database Issues
```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Connect to database
docker-compose exec postgres psql -U postgres -d stock_screener
```

## 📈 Next Steps

1. **Add More Stocks**: Use the `/stocks/add` endpoint
2. **Explore API**: Visit http://localhost:8000/docs
3. **Custom Screening**: Modify screening criteria in the code
4. **News Sources**: Add your Brave Search API key for more news
5. **Model Optimization**: Experiment with different Ollama models

## 🛑 When Done

```bash
# Stop all services
./start_with_docker.sh stop

# Or clean up completely
./start_with_docker.sh clean
```

---

**🎉 That's it!** You now have a fully functional AI-powered stock screener running locally with your own LLM models. 