export interface Stock {
  symbol: string;
  name: string;
  sector: string;
  industry: string;
  market_cap: number;
  currency: string;
  asset_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StockMetrics {
  date: string;
  pe_ratio?: number;
  pb_ratio?: number;
  ps_ratio?: number;
  ev_to_ebitda?: number;
  roe?: number;
  roa?: number;
  gross_margin?: number;
  operating_margin?: number;
  net_margin?: number;
  revenue_growth_yoy?: number;
  earnings_growth_yoy?: number;
  debt_to_equity?: number;
  current_ratio?: number;
  quick_ratio?: number;
  dividend_yield?: number;
  dividend_payout_ratio?: number;
  beta?: number;
  book_value_per_share?: number;
  earnings_per_share?: number;
}

export interface HistoricalData {
  date: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  dividend_amount: number;
  split_coefficient: number;
}

export interface StockDetails extends Stock {
  current_price?: number;
  metrics?: StockMetrics;
  historical_data?: HistoricalData[];
  growth_metrics?: {
    cagr_1y: number;
    cagr_5y: number;
    volatility: number;
    max_drawdown: number;
    sharpe_ratio: number;
  };
}

export interface AddStockRequest {
  symbol: string;
  name?: string;
}

export interface AddStockResponse {
  message: string;
  symbol: string;
  name?: string;
}

export interface StockSearchResult {
  symbol: string;
  name: string;
  price?: number;
  change?: number;
  change_percent?: number;
  market_cap?: number;
  sector?: string;
} 