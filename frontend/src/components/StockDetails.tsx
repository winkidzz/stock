import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
  Close as CloseIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { Stock, StockDetails as StockDetailsType, StockMetrics, HistoricalData } from '../types/stock';
import { stockApi } from '../services/api';
import {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatDate,
  formatVolume,
  getChangeColor,
} from '../utils/formatters';

interface StockDetailsProps {
  stock: Stock | null;
  open: boolean;
  onClose: () => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`stock-tabpanel-${index}`}
      aria-labelledby={`stock-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
};

export const StockDetails: React.FC<StockDetailsProps> = ({ stock, open, onClose }) => {
  const [stockDetails, setStockDetails] = useState<StockDetailsType | null>(null);
  const [metrics, setMetrics] = useState<StockMetrics[]>([]);
  const [historicalData, setHistoricalData] = useState<HistoricalData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    if (stock && open) {
      fetchStockDetails();
    }
  }, [stock, open]);

  const fetchStockDetails = async () => {
    if (!stock) return;

    try {
      setLoading(true);
      setError(null);

      // Fetch all data in parallel
      const [detailsResponse, metricsResponse, historicalResponse] = await Promise.allSettled([
        stockApi.getStock(stock.symbol),
        stockApi.getStockMetrics(stock.symbol),
        stockApi.getHistoricalData(stock.symbol, 1), // 1 year of data
      ]);

      if (detailsResponse.status === 'fulfilled') {
        setStockDetails(detailsResponse.value);
      }

      if (metricsResponse.status === 'fulfilled') {
        setMetrics(metricsResponse.value);
      }

      if (historicalResponse.status === 'fulfilled') {
        setHistoricalData(historicalResponse.value.slice(0, 10)); // Show last 10 days
      }

    } catch (err: any) {
      console.error('Error fetching stock details:', err);
      setError(err.response?.data?.detail || 'Failed to fetch stock details');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const renderOverview = () => (
    <Box display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={3}>
      <Box flex={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Company Information</Typography>
            <Box mb={2}>
              <Typography variant="body2" color="textSecondary">Symbol</Typography>
              <Typography variant="h5" color="primary" fontWeight="bold">
                {stock?.symbol}
              </Typography>
            </Box>
            <Box mb={2}>
              <Typography variant="body2" color="textSecondary">Company Name</Typography>
              <Typography variant="h6">{stock?.name}</Typography>
            </Box>
            <Box mb={2}>
              <Typography variant="body2" color="textSecondary">Sector</Typography>
              <Chip label={stock?.sector} color="primary" variant="outlined" />
            </Box>
            <Box mb={2}>
              <Typography variant="body2" color="textSecondary">Industry</Typography>
              <Typography variant="body1">{stock?.industry}</Typography>
            </Box>
            <Box mb={2}>
              <Typography variant="body2" color="textSecondary">Market Cap</Typography>
              <Typography variant="h6">{formatCurrency(stock?.market_cap)}</Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>

      <Box flex={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Current Metrics</Typography>
            {stockDetails?.current_price && (
              <Box mb={2}>
                <Typography variant="body2" color="textSecondary">Current Price</Typography>
                <Typography variant="h5" color="primary" fontWeight="bold">
                  {formatCurrency(stockDetails.current_price)}
                </Typography>
              </Box>
            )}
            {stockDetails?.growth_metrics && (
              <>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">1Y CAGR</Typography>
                  <Typography 
                    variant="h6" 
                    style={{ color: getChangeColor(stockDetails.growth_metrics.cagr_1y * 100) }}
                  >
                    {formatPercentage(stockDetails.growth_metrics.cagr_1y * 100)}
                  </Typography>
                </Box>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">5Y CAGR</Typography>
                  <Typography 
                    variant="h6"
                    style={{ color: getChangeColor(stockDetails.growth_metrics.cagr_5y * 100) }}
                  >
                    {formatPercentage(stockDetails.growth_metrics.cagr_5y * 100)}
                  </Typography>
                </Box>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">Volatility</Typography>
                  <Typography variant="body1">
                    {formatPercentage(stockDetails.growth_metrics.volatility * 100)}
                  </Typography>
                </Box>
                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary">Sharpe Ratio</Typography>
                  <Typography variant="body1">
                    {formatNumber(stockDetails.growth_metrics.sharpe_ratio)}
                  </Typography>
                </Box>
              </>
                         )}
           </CardContent>
         </Card>
       </Box>
     </Box>
   );

  const renderMetrics = () => {
    const latestMetrics = metrics.length > 0 ? metrics[0] : null;

    if (!latestMetrics) {
      return (
        <Alert severity="info">
          No financial metrics available for this stock.
        </Alert>
      );
    }

    const metricRows = [
      { label: 'P/E Ratio', value: formatNumber(latestMetrics.pe_ratio) },
      { label: 'P/B Ratio', value: formatNumber(latestMetrics.pb_ratio) },
      { label: 'P/S Ratio', value: formatNumber(latestMetrics.ps_ratio) },
      { label: 'EV/EBITDA', value: formatNumber(latestMetrics.ev_to_ebitda) },
      { label: 'ROE', value: formatPercentage(latestMetrics.roe) },
      { label: 'ROA', value: formatPercentage(latestMetrics.roa) },
      { label: 'Gross Margin', value: formatPercentage(latestMetrics.gross_margin) },
      { label: 'Operating Margin', value: formatPercentage(latestMetrics.operating_margin) },
      { label: 'Net Margin', value: formatPercentage(latestMetrics.net_margin) },
      { label: 'Debt to Equity', value: formatNumber(latestMetrics.debt_to_equity) },
      { label: 'Current Ratio', value: formatNumber(latestMetrics.current_ratio) },
      { label: 'Beta', value: formatNumber(latestMetrics.beta) },
      { label: 'Dividend Yield', value: formatPercentage(latestMetrics.dividend_yield) },
      { label: 'EPS', value: formatCurrency(latestMetrics.earnings_per_share) },
    ];

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Financial Metrics
            <Typography variant="caption" color="textSecondary" ml={2}>
              As of {formatDate(latestMetrics.date)}
            </Typography>
          </Typography>
          <Box 
            display="grid" 
            gridTemplateColumns={{ 
              xs: 'repeat(2, 1fr)', 
              md: 'repeat(4, 1fr)', 
              lg: 'repeat(4, 1fr)' 
            }} 
            gap={2}
          >
            {metricRows.map((metric, index) => (
              <Box key={index}>
                <Typography variant="body2" color="textSecondary">
                  {metric.label}
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {metric.value}
                </Typography>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderHistoricalData = () => (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>Recent Price History</Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell align="right">Open</TableCell>
                <TableCell align="right">High</TableCell>
                <TableCell align="right">Low</TableCell>
                <TableCell align="right">Close</TableCell>
                <TableCell align="right">Volume</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {historicalData.map((day, index) => (
                <TableRow key={index}>
                  <TableCell>{formatDate(day.date)}</TableCell>
                  <TableCell align="right">{formatCurrency(day.open_price)}</TableCell>
                  <TableCell align="right">{formatCurrency(day.high_price)}</TableCell>
                  <TableCell align="right">{formatCurrency(day.low_price)}</TableCell>
                  <TableCell align="right">{formatCurrency(day.close_price)}</TableCell>
                  <TableCell align="right">{formatVolume(day.volume)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        {historicalData.length === 0 && (
          <Alert severity="info" sx={{ mt: 2 }}>
            No historical data available for this stock.
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  if (!stock) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            {stock.symbol} - {stock.name}
          </Typography>
          <Box>
            <IconButton onClick={fetchStockDetails} disabled={loading}>
              <RefreshIcon />
            </IconButton>
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading && (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
            <Typography variant="body1" ml={2}>Loading stock details...</Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && (
          <>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="stock details tabs">
              <Tab label="Overview" />
              <Tab label="Metrics" />
              <Tab label="Historical Data" />
            </Tabs>

            <TabPanel value={tabValue} index={0}>
              {renderOverview()}
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              {renderMetrics()}
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              {renderHistoricalData()}
            </TabPanel>
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} color="primary">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default StockDetails; 