import axios from 'axios';
import {
  Stock,
  StockDetails,
  StockMetrics,
  HistoricalData,
  AddStockRequest,
  AddStockResponse,
  StockSearchResult
} from '../types/stock';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const stockApi = {
  // Get all stocks
  getAllStocks: async (): Promise<Stock[]> => {
    const response = await api.get('/stocks');
    return response.data;
  },

  // Get specific stock by symbol
  getStock: async (symbol: string): Promise<StockDetails> => {
    const response = await api.get(`/stocks/${symbol.toUpperCase()}`);
    return response.data;
  },

  // Add new stock
  addStock: async (request: AddStockRequest): Promise<AddStockResponse> => {
    const response = await api.post('/stocks/add', request);
    return response.data;
  },

  // Get stock metrics
  getStockMetrics: async (symbol: string): Promise<StockMetrics[]> => {
    const response = await api.get(`/stocks/${symbol.toUpperCase()}/metrics`);
    return response.data;
  },

  // Get historical data
  getHistoricalData: async (symbol: string, years?: number): Promise<HistoricalData[]> => {
    const params = years ? { years } : {};
    const response = await api.get(`/stocks/${symbol.toUpperCase()}/historical`, { params });
    return response.data;
  },

  // Update stock data
  updateStock: async (symbol: string): Promise<{ message: string }> => {
    const response = await api.post(`/stocks/${symbol.toUpperCase()}/update`);
    return response.data;
  },

  // Delete stock
  deleteStock: async (symbol: string): Promise<{ message: string }> => {
    const response = await api.delete(`/stocks/${symbol.toUpperCase()}`);
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await api.get('/health');
    return response.data;
  },

  // Search for stocks (real-time external search)
  searchStocks: async (query: string): Promise<StockSearchResult[]> => {
    // This would be a new endpoint for real-time search
    // For now, we'll simulate it
    try {
      const response = await api.get(`/stocks/search?q=${encodeURIComponent(query)}`);
      return response.data;
    } catch (error) {
      // Fallback to mock data if endpoint doesn't exist yet
      console.log('Search endpoint not available, using mock data');
      return mockSearchResults(query);
    }
  },
};

// Mock search results for demonstration
const mockSearchResults = (query: string): StockSearchResult[] => {
  const mockStocks = [
    { symbol: 'AAPL', name: 'Apple Inc.', price: 175.43, change: 2.15, change_percent: 1.24, market_cap: 2800000000000, sector: 'Technology' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 2847.51, change: -15.23, change_percent: -0.53, market_cap: 1800000000000, sector: 'Technology' },
    { symbol: 'MSFT', name: 'Microsoft Corporation', price: 378.85, change: 5.67, change_percent: 1.52, market_cap: 2900000000000, sector: 'Technology' },
    { symbol: 'TSLA', name: 'Tesla, Inc.', price: 248.42, change: -8.91, change_percent: -3.46, market_cap: 790000000000, sector: 'Automotive' },
    { symbol: 'NVDA', name: 'NVIDIA Corporation', price: 589.35, change: 12.45, change_percent: 2.16, market_cap: 1450000000000, sector: 'Technology' },
    { symbol: 'AMZN', name: 'Amazon.com, Inc.', price: 3342.88, change: -22.15, change_percent: -0.66, market_cap: 1700000000000, sector: 'Consumer Discretionary' },
  ];

  return mockStocks.filter(stock => 
    stock.symbol.toLowerCase().includes(query.toLowerCase()) ||
    stock.name.toLowerCase().includes(query.toLowerCase())
  );
};

export default api; 