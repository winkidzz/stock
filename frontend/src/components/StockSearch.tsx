import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  CircularProgress,
  Alert,
  Paper,
  InputAdornment,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Close as CloseIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { StockSearchResult, AddStockRequest } from '../types/stock';
import { stockApi } from '../services/api';
import { formatCurrency, formatPercentage, getChangeColor } from '../utils/formatters';

interface StockSearchProps {
  open: boolean;
  onClose: () => void;
  onStockAdded?: (symbol: string) => void;
}

export const StockSearch: React.FC<StockSearchProps> = ({ open, onClose, onStockAdded }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<StockSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addingStock, setAddingStock] = useState<string | null>(null);

  // Debounce search function
  const debounceSearch = useCallback(
    debounce((query: string) => {
      if (query.trim().length >= 2) {
        performSearch(query);
      } else {
        setSearchResults([]);
      }
    }, 500),
    []
  );

  useEffect(() => {
    if (searchQuery) {
      debounceSearch(searchQuery);
    } else {
      setSearchResults([]);
    }
  }, [searchQuery, debounceSearch]);

  const performSearch = async (query: string) => {
    try {
      setLoading(true);
      setError(null);
      const results = await stockApi.searchStocks(query);
      setSearchResults(results);
    } catch (err: any) {
      console.error('Search error:', err);
      setError('Failed to search stocks. Please try again.');
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddStock = async (stock: StockSearchResult) => {
    try {
      setAddingStock(stock.symbol);
      setError(null);

      const request: AddStockRequest = {
        symbol: stock.symbol,
        name: stock.name,
      };

      await stockApi.addStock(request);
      
      // Notify parent component
      onStockAdded?.(stock.symbol);
      
      // Show success message briefly then close
      setTimeout(() => {
        onClose();
        setSearchQuery('');
        setSearchResults([]);
      }, 1000);

    } catch (err: any) {
      console.error('Error adding stock:', err);
      setError(err.response?.data?.detail || 'Failed to add stock');
    } finally {
      setAddingStock(null);
    }
  };

  const handleClose = () => {
    onClose();
    setSearchQuery('');
    setSearchResults([]);
    setError(null);
  };

  const renderStockResult = (stock: StockSearchResult) => {
    const isAdding = addingStock === stock.symbol;
    
    return (
      <ListItem key={stock.symbol} divider>
        <ListItemText
          primary={
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="subtitle1" fontWeight="bold" color="primary">
                {stock.symbol}
              </Typography>
              <Typography variant="body1">
                {stock.name}
              </Typography>
              {stock.sector && (
                <Chip 
                  label={stock.sector} 
                  size="small" 
                  variant="outlined" 
                  color="primary"
                />
              )}
            </Box>
          }
          secondary={
            <Box display="flex" alignItems="center" gap={2} mt={1}>
              {stock.price && (
                <Typography variant="body2">
                  <strong>Price:</strong> {formatCurrency(stock.price)}
                </Typography>
              )}
              {stock.change !== undefined && (
                <Box display="flex" alignItems="center" gap={0.5}>
                  {stock.change >= 0 ? <TrendingUpIcon color="success" fontSize="small" /> : <TrendingDownIcon color="error" fontSize="small" />}
                  <Typography 
                    variant="body2" 
                    style={{ color: getChangeColor(stock.change) }}
                  >
                    {stock.change >= 0 ? '+' : ''}{formatCurrency(stock.change)}
                    {stock.change_percent !== undefined && (
                      <span> ({formatPercentage(stock.change_percent)})</span>
                    )}
                  </Typography>
                </Box>
              )}
              {stock.market_cap && (
                <Typography variant="body2">
                  <strong>Market Cap:</strong> {formatCurrency(stock.market_cap)}
                </Typography>
              )}
            </Box>
          }
        />
        <ListItemSecondaryAction>
          <IconButton 
            onClick={() => handleAddStock(stock)}
            disabled={isAdding}
            color="primary"
            size="large"
          >
            {isAdding ? <CircularProgress size={24} /> : <AddIcon />}
          </IconButton>
        </ListItemSecondaryAction>
      </ListItem>
    );
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Search & Add Stocks</Typography>
          <IconButton onClick={handleClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box mb={3}>
          <TextField
            fullWidth
            placeholder="Search stocks by symbol or company name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: loading && (
                <InputAdornment position="end">
                  <CircularProgress size={20} />
                </InputAdornment>
              ),
            }}
            variant="outlined"
          />
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {addingStock && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Adding {addingStock} to your portfolio...
          </Alert>
        )}

        <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
          {searchResults.length > 0 ? (
            <List>
              {searchResults.map(renderStockResult)}
            </List>
          ) : searchQuery.trim().length >= 2 && !loading ? (
            <Box p={3} textAlign="center">
              <Typography variant="body1" color="textSecondary">
                No stocks found for "{searchQuery}"
              </Typography>
              <Typography variant="body2" color="textSecondary" mt={1}>
                Try searching with a stock symbol (e.g., AAPL) or company name
              </Typography>
            </Box>
          ) : !loading ? (
            <Box p={3} textAlign="center">
              <Typography variant="body1" color="textSecondary">
                Enter at least 2 characters to search for stocks
              </Typography>
            </Box>
          ) : null}
        </Paper>

        {searchQuery.trim().length >= 2 && (
          <Box mt={2}>
            <Typography variant="caption" color="textSecondary">
              Search results are updated in real-time. Click the + button to add a stock to your portfolio.
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

// Debounce utility function
function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

export default StockSearch; 