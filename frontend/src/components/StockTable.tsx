import React, { useState, useEffect } from 'react';
import {
  DataGrid,
  GridColDef,
  GridRowParams,
  GridActionsCellItem,
  GridRowId,
} from '@mui/x-data-grid';
import {
  Box,
  Chip,
  IconButton,
  Tooltip,
  Paper,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { Stock } from '../types/stock';
import { stockApi } from '../services/api';
import { formatCurrency, formatDate, formatNumber } from '../utils/formatters';

interface StockTableProps {
  onStockSelect: (stock: Stock) => void;
  onRefresh?: () => void;
}

export const StockTable: React.FC<StockTableProps> = ({ onStockSelect, onRefresh }) => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStocks = async () => {
    try {
      setLoading(true);
      setError(null);
      const stockData = await stockApi.getAllStocks();
      setStocks(stockData);
    } catch (err: any) {
      console.error('Error fetching stocks:', err);
      setError(err.response?.data?.detail || 'Failed to fetch stocks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStocks();
  }, []);

  const handleRefresh = () => {
    fetchStocks();
    onRefresh?.();
  };

  const handleDelete = async (symbol: string) => {
    if (window.confirm(`Are you sure you want to delete ${symbol}?`)) {
      try {
        await stockApi.deleteStock(symbol);
        setStocks(stocks.filter(stock => stock.symbol !== symbol));
      } catch (err: any) {
        console.error('Error deleting stock:', err);
        setError(err.response?.data?.detail || 'Failed to delete stock');
      }
    }
  };

  const handleUpdate = async (symbol: string) => {
    try {
      await stockApi.updateStock(symbol);
      // Refresh the table after update
      fetchStocks();
    } catch (err: any) {
      console.error('Error updating stock:', err);
      setError(err.response?.data?.detail || 'Failed to update stock');
    }
  };

  const renderSectorChip = (sector: string) => {
    const getSectorColor = (sector: string) => {
      switch (sector.toLowerCase()) {
        case 'technology': return 'primary';
        case 'healthcare': return 'secondary';
        case 'financial services': return 'success';
        case 'consumer discretionary': return 'warning';
        case 'communication services': return 'info';
        case 'industrials': return 'default';
        default: return 'default';
      }
    };

    return (
      <Chip 
        label={sector} 
        size="small" 
        color={getSectorColor(sector) as any}
        variant="outlined"
      />
    );
  };

  const columns: GridColDef[] = [
    {
      field: 'symbol',
      headerName: 'Symbol',
      width: 100,
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="bold" color="primary">
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'name',
      headerName: 'Company Name',
      width: 250,
      renderCell: (params) => (
        <Tooltip title={params.value}>
          <Typography variant="body2" noWrap>
            {params.value}
          </Typography>
        </Tooltip>
      ),
    },
    {
      field: 'sector',
      headerName: 'Sector',
      width: 180,
      renderCell: (params) => renderSectorChip(params.value),
    },
    {
      field: 'industry',
      headerName: 'Industry',
      width: 200,
      renderCell: (params) => (
        <Tooltip title={params.value}>
          <Typography variant="body2" noWrap>
            {params.value}
          </Typography>
        </Tooltip>
      ),
    },
    {
      field: 'market_cap',
      headerName: 'Market Cap',
      width: 120,
      type: 'number',
      renderCell: (params) => (
        <Typography variant="body2">
          {formatCurrency(params.value)}
        </Typography>
      ),
    },
    {
      field: 'currency',
      headerName: 'Currency',
      width: 100,
    },
    {
      field: 'asset_type',
      headerName: 'Type',
      width: 100,
      renderCell: (params) => (
        <Chip 
          label={params.value.toUpperCase()} 
          size="small" 
          variant="filled"
          color="default"
        />
      ),
    },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 100,
      renderCell: (params) => (
        <Chip 
          label={params.value ? 'Active' : 'Inactive'} 
          size="small" 
          color={params.value ? 'success' : 'error'}
          variant="filled"
        />
      ),
    },
    {
      field: 'updated_at',
      headerName: 'Last Updated',
      width: 130,
      renderCell: (params) => (
        <Typography variant="body2">
          {formatDate(params.value)}
        </Typography>
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 120,
      getActions: (params: GridRowParams) => [
        <GridActionsCellItem
          icon={
            <Tooltip title="View Details">
              <VisibilityIcon />
            </Tooltip>
          }
          label="View"
          onClick={() => onStockSelect(params.row as Stock)}
        />,
        <GridActionsCellItem
          icon={
            <Tooltip title="Update Data">
              <RefreshIcon />
            </Tooltip>
          }
          label="Update"
          onClick={() => handleUpdate(params.row.symbol)}
        />,
        <GridActionsCellItem
          icon={
            <Tooltip title="Delete Stock">
              <DeleteIcon />
            </Tooltip>
          }
          label="Delete"
          onClick={() => handleDelete(params.row.symbol)}
          showInMenu
        />,
      ],
    },
  ];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={400}>
        <CircularProgress />
        <Typography variant="h6" ml={2}>Loading stocks...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <IconButton color="inherit" size="small" onClick={handleRefresh}>
          <RefreshIcon />
        </IconButton>
      }>
        {error}
      </Alert>
    );
  }

  return (
    <Paper elevation={2}>
      <Box p={2}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Stock Portfolio ({stocks.length} stocks)
          </Typography>
          <IconButton onClick={handleRefresh} color="primary">
            <RefreshIcon />
          </IconButton>
        </Box>
        
        <Box height={600}>
          <DataGrid
            rows={stocks}
            columns={columns}
            getRowId={(row) => row.symbol}
            initialState={{
              pagination: {
                paginationModel: { page: 0, pageSize: 25 },
              },
              sorting: {
                sortModel: [{ field: 'market_cap', sort: 'desc' }],
              },
            }}
            pageSizeOptions={[10, 25, 50, 100]}
            checkboxSelection={false}
            disableRowSelectionOnClick
            onRowDoubleClick={(params) => onStockSelect(params.row as Stock)}
            sx={{
              '& .MuiDataGrid-row:hover': {
                backgroundColor: 'rgba(25, 118, 210, 0.04)',
              },
              '& .MuiDataGrid-cell:focus': {
                outline: 'none',
              },
            }}
          />
        </Box>
      </Box>
    </Paper>
  );
};

export default StockTable; 