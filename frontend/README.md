# Stock Screening Dashboard - React Frontend

A modern React TypeScript frontend for the LangChain + LangGraph stock screening application, designed to help find investments capable of turning $10,000 into $2 million in 10 years (34.9% CAGR).

## 🎯 Features

### 📊 **Stock Management**
- **Interactive Stock Table**: Sortable data grid showing all portfolio stocks
- **Real-time Data**: Live stock information with automatic refresh
- **Detailed Stock Views**: Comprehensive modal with metrics, historical data, and growth analysis
- **Smart Filtering**: Filter by sector, industry, market cap, and more

### 🔍 **Search & Discovery**
- **Real-time Stock Search**: Find stocks by symbol or company name
- **Auto-complete Suggestions**: Intelligent search with live results
- **One-click Addition**: Add stocks directly from search results
- **Market Data Preview**: See price, change, and market cap before adding

### 📈 **Financial Analysis**
- **Key Metrics Display**: P/E ratio, market cap, ROE, debt-to-equity, and more
- **Growth Metrics**: CAGR, volatility, Sharpe ratio, max drawdown
- **Historical Data**: Recent price history with volume analysis
- **Performance Tracking**: Track investment performance over time

### 🎨 **Modern UI/UX**
- **Material-UI Design**: Professional, responsive interface
- **Dark/Light Themes**: Adaptive color schemes
- **Mobile Responsive**: Works seamlessly on all devices
- **Intuitive Navigation**: Easy-to-use floating action buttons

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Docker (for full stack deployment)
- Backend API running on port 8000

### Development Setup

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Start Development Server**
```bash
npm start
```

3. **Access Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Docker Deployment

1. **Build and Run Full Stack**
```bash
# From project root
docker-compose up -d --build
```

2. **Access Services**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Database: localhost:5433

## 📱 User Guide

### 1. **Viewing Stock Portfolio**
- **Main Table**: See all your stocks with key metrics
- **Sorting**: Click column headers to sort data
- **Actions**: Use row action buttons to view details, update, or delete
- **Double-click**: Open detailed view for any stock

### 2. **Adding New Stocks**
- **Search Button**: Click the floating search button (🔍)
- **Type Symbol/Name**: Enter stock symbol (e.g., "AAPL") or company name
- **Select Result**: Click the + button next to desired stock
- **Auto-refresh**: Table updates automatically after adding

### 3. **Stock Details**
- **Overview Tab**: Company information and key metrics
- **Metrics Tab**: Comprehensive financial ratios and indicators
- **Historical Tab**: Recent price data and volume analysis
- **Refresh Data**: Update stock information with refresh button

### 4. **Search Features**
- **Real-time Search**: Results update as you type
- **Multiple Formats**: Search by symbol, company name, or keywords
- **Market Preview**: See current price and daily change
- **Sector Filtering**: Results show sector and industry information

## 🛠 Technical Architecture

### **Frontend Stack**
- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Full type safety and enhanced developer experience
- **Material-UI**: Professional component library with theming
- **Axios**: HTTP client for API communication

### **Key Components**
- `StockTable`: Main data grid with sorting and actions
- `StockDetails`: Comprehensive stock information modal
- `StockSearch`: Real-time search and add functionality
- `App`: Main application shell with state management

### **API Integration**
- RESTful API communication with FastAPI backend
- Error handling and loading states
- Optimistic updates for better UX
- Real-time data synchronization

## 🔧 Configuration

### **Environment Variables**
```bash
REACT_APP_API_URL=http://localhost:8000    # Backend API URL
REACT_APP_NAME=Stock Screening Dashboard   # App display name
GENERATE_SOURCEMAP=false                   # Disable sourcemaps in production
```

### **API Endpoints Used**
- `GET /stocks` - List all stocks
- `GET /stocks/{symbol}` - Get stock details
- `POST /stocks/add` - Add new stock
- `GET /stocks/{symbol}/metrics` - Get financial metrics
- `GET /stocks/{symbol}/historical` - Get historical data
- `GET /stocks/search` - Search for stocks (with fallback)

## 📊 Data Display

### **Stock Table Columns**
- **Symbol**: Stock ticker symbol (clickable)
- **Company Name**: Full company name with tooltip
- **Sector**: Color-coded sector chips
- **Industry**: Industry classification
- **Market Cap**: Formatted currency (B/M/K notation)
- **Currency**: Trading currency
- **Type**: Asset type (stock, ETF, etc.)
- **Status**: Active/Inactive indicator
- **Last Updated**: Data freshness timestamp
- **Actions**: View, Update, Delete operations

### **Detailed Metrics**
- **Valuation**: P/E, P/B, P/S, EV/EBITDA ratios
- **Profitability**: ROE, ROA, Gross/Operating/Net margins
- **Growth**: Revenue growth, earnings growth YoY
- **Financial Health**: Debt-to-equity, current ratio, quick ratio
- **Dividends**: Yield, payout ratio
- **Risk**: Beta, volatility, max drawdown

## 🎨 UI Features

### **Visual Enhancements**
- **Color-coded Metrics**: Green for positive, red for negative changes
- **Sector Chips**: Different colors for different sectors
- **Status Indicators**: Clear active/inactive status
- **Loading States**: Smooth loading animations
- **Error Handling**: User-friendly error messages

### **Responsive Design**
- **Mobile-first**: Optimized for mobile devices
- **Tablet Support**: Adapted layouts for tablets
- **Desktop**: Full feature set on larger screens
- **Accessibility**: WCAG compliant with keyboard navigation

## 🔄 Development

### **Available Scripts**
```bash
npm start          # Development server
npm build          # Production build
npm test           # Run tests
npm run eject      # Eject from Create React App
```

### **Docker Commands**
```bash
# Development with hot reload
docker-compose up frontend

# Production build
docker build -f Dockerfile -t stock-frontend .

# Run production container
docker run -p 3000:80 stock-frontend
```

## 🚦 Status & Performance

### **Current Features** ✅
- ✅ Stock table with sorting and filtering
- ✅ Real-time search and add functionality  
- ✅ Detailed stock information modals
- ✅ Financial metrics display
- ✅ Historical data visualization
- ✅ Responsive Material-UI design
- ✅ Error handling and loading states
- ✅ Docker containerization

### **Future Enhancements** 🚧
- 📊 Interactive charts and graphs
- 📱 Push notifications for price alerts
- 💾 Local storage for user preferences
- 🔍 Advanced filtering and search
- 📈 Portfolio performance analytics
- 🔔 Real-time price updates via WebSocket

## 🐛 Troubleshooting

### **Common Issues**

1. **Frontend can't connect to backend**
   - Ensure backend is running on port 8000
   - Check CORS configuration in FastAPI
   - Verify `REACT_APP_API_URL` environment variable

2. **Search not working**
   - Search endpoint may not be implemented yet
   - Currently uses mock data as fallback
   - Check browser console for API errors

3. **Stock data appears empty**
   - Backend may need time to collect data
   - Try updating stock data using refresh button
   - Check backend logs for scraping errors

4. **Build failures**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Update dependencies: `npm update`
   - Check Node.js version compatibility

## 📞 Support

For issues and questions:
- Check browser console for error messages
- Review backend API logs: `docker logs stock-api-1`
- Verify all containers are running: `docker-compose ps`
- Test API endpoints directly with curl

---

**Stock Screening Dashboard** - Powered by LangChain, LangGraph, and Local LLMs  
Built with ❤️ using React, TypeScript, and Material-UI
