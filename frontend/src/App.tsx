import React, { useState } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Fab,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
} from '@mui/icons-material';

import StockTable from './components/StockTable';
import StockDetails from './components/StockDetails';
import StockSearch from './components/StockSearch';
import { Stock } from './types/stock';

// Create Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
});

function App() {
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });
  const [refreshKey, setRefreshKey] = useState(0);

  const handleStockSelect = (stock: Stock) => {
    setSelectedStock(stock);
    setDetailsOpen(true);
  };

  const handleDetailsClose = () => {
    setDetailsOpen(false);
    setSelectedStock(null);
  };

  const handleSearchClose = () => {
    setSearchOpen(false);
  };

  const handleStockAdded = (symbol: string) => {
    setSnackbar({
      open: true,
      message: `Successfully added ${symbol} to your portfolio!`,
      severity: 'success',
    });
    
    // Trigger refresh of stock table
    setRefreshKey(prev => prev + 1);
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const handleSnackbarClose = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      {/* App Bar */}
      <AppBar position="static" elevation={2}>
        <Toolbar>
          <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
            📈 Stock Screening Dashboard
          </Typography>
          <Typography variant="subtitle1" color="inherit">
            LangChain + LangGraph Stock Analysis
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Box mb={3}>
          <Typography variant="h5" gutterBottom>
            Investment Portfolio Manager
          </Typography>
          <Typography variant="body1" color="textSecondary" paragraph>
            Find investments capable of turning $10,000 into $2 million in 10 years (34.9% CAGR).
            View detailed metrics, add new stocks, and analyze growth potential.
          </Typography>
        </Box>

        {/* Stock Table */}
        <StockTable 
          key={refreshKey}
          onStockSelect={handleStockSelect} 
          onRefresh={handleRefresh}
        />

        {/* Floating Action Buttons */}
        <Box 
          position="fixed" 
          bottom={24} 
          right={24}
          display="flex"
          flexDirection="column"
          gap={2}
        >
          <Fab 
            color="primary" 
            onClick={() => setSearchOpen(true)}
            sx={{ boxShadow: 3 }}
          >
            <SearchIcon />
          </Fab>
        </Box>

        {/* Stock Details Modal */}
        <StockDetails
          stock={selectedStock}
          open={detailsOpen}
          onClose={handleDetailsClose}
        />

        {/* Stock Search Modal */}
        <StockSearch
          open={searchOpen}
          onClose={handleSearchClose}
          onStockAdded={handleStockAdded}
        />

        {/* Success/Error Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleSnackbarClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        >
          <Alert 
            onClose={handleSnackbarClose} 
            severity={snackbar.severity}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>

      {/* Footer */}
      <Box 
        component="footer" 
        sx={{ 
          mt: 'auto', 
          py: 3, 
          px: 2, 
          bgcolor: 'background.paper',
          borderTop: 1,
          borderColor: 'divider'
        }}
      >
        <Container maxWidth="xl">
          <Typography variant="body2" color="textSecondary" align="center">
            © 2024 Stock Screening Dashboard. Powered by LangChain, LangGraph, and Local LLMs.
          </Typography>
          <Typography variant="caption" color="textSecondary" align="center" display="block" mt={1}>
            Data sourced via Yahoo Finance with Playwright fallback • Real-time analysis via Ollama
          </Typography>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
