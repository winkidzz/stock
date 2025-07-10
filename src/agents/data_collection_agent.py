from typing import Dict, List, Optional, TypedDict
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import asyncio

from langchain.agents import Tool
from langchain.schema import HumanMessage, SystemMessage
from langchain_ollama import OllamaLLM
from langchain.tools import BaseTool
from langgraph.graph import StateGraph, END

from ..services.stock_data_service import stock_data_service
from ..services.news_service import news_service
from ..database import get_db_session, Stock, HistoricalData, FinancialMetrics, NewsArticle
from ..config import settings

logger = logging.getLogger(__name__)

class DataCollectionState(TypedDict):
    """State for data collection agent"""
    symbol: str
    stock_name: str
    task: str
    collected_data: Dict
    status: str
    error: Optional[str]
    next_action: str

@dataclass
class CollectionResult:
    success: bool
    data: Dict
    error: Optional[str] = None

class StockDataCollectionTool(BaseTool):
    """Tool for collecting stock data"""
    name = "stock_data_collection"
    description = "Collect historical stock data and financial metrics for a given symbol"
    
    def _run(self, symbol: str, stock_name: str = None) -> CollectionResult:
        """Collect stock data synchronously"""
        try:
            # Get stock info
            stock_info = stock_data_service.get_stock_info(symbol)
            
            # Get historical data
            historical_data = stock_data_service.get_historical_data(symbol)
            
            # Get financial metrics
            financial_metrics = stock_data_service.get_financial_metrics(symbol)
            
            # Calculate growth metrics
            growth_metrics = stock_data_service.calculate_growth_metrics(symbol, historical_data)
            
            # Save to database (this will create a basic record even if stock_info is None)
            success = stock_data_service.save_stock_data(symbol, stock_name)
            
            return CollectionResult(
                success=success,
                data={
                    "stock_info": stock_info,
                    "historical_data_points": len(historical_data),
                    "financial_metrics": financial_metrics,
                    "growth_metrics": growth_metrics,
                    "data_saved": success
                }
            )
        except Exception as e:
            logger.error(f"Error in stock data collection: {e}")
            return CollectionResult(
                success=False,
                data={},
                error=str(e)
            )
    
    async def _arun(self, symbol: str, stock_name: str = None) -> CollectionResult:
        """Async version of stock data collection"""
        return await asyncio.to_thread(self._run, symbol, stock_name)

class NewsCollectionTool(BaseTool):
    """Tool for collecting news data"""
    name = "news_collection"
    description = "Collect and analyze news articles for a given stock symbol"
    
    def _run(self, symbol: str, stock_name: str) -> CollectionResult:
        """Collect news data synchronously"""
        try:
            # Run in new event loop to avoid async conflicts
            return asyncio.run(self._collect_news_async(symbol, stock_name))
        except Exception as e:
            logger.error(f"Error in news collection: {e}")
            return CollectionResult(
                success=False,
                data={},
                error=str(e)
            )
    
    async def _collect_news_async(self, symbol: str, stock_name: str) -> CollectionResult:
        """Async news collection"""
        try:
            # Collect news
            news_items = await news_service.collect_stock_news(symbol, stock_name)
            
            # Save to database
            success = await news_service.save_news_to_db(symbol, news_items)
            
            # Get news summary
            news_summary = await news_service.get_news_summary(symbol)
            
            return CollectionResult(
                success=success,
                data={
                    "news_items_collected": len(news_items),
                    "news_summary": news_summary,
                    "data_saved": success
                }
            )
        except Exception as e:
            logger.error(f"Error in async news collection: {e}")
            return CollectionResult(
                success=False,
                data={},
                error=str(e)
            )
    
    async def _arun(self, symbol: str, stock_name: str) -> CollectionResult:
        """Async version of news collection"""
        return await self._collect_news_async(symbol, stock_name)

class DataValidationTool(BaseTool):
    """Tool for validating collected data"""
    name = "data_validation"
    description = "Validate the completeness and quality of collected data"
    
    def _run(self, symbol: str) -> CollectionResult:
        """Validate data synchronously"""
        try:
            with get_db_session() as db:
                # Check if stock exists
                stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
                if not stock:
                    return CollectionResult(
                        success=False,
                        data={},
                        error=f"Stock {symbol} not found in database"
                    )
                
                # Check historical data
                historical_count = db.query(HistoricalData).filter(
                    HistoricalData.stock_id == stock.id
                ).count()
                
                # Check financial metrics
                financial_metrics_count = db.query(FinancialMetrics).filter(
                    FinancialMetrics.stock_id == stock.id
                ).count()
                
                # Check recent news
                recent_news_count = db.query(NewsArticle).filter(
                    NewsArticle.stock_id == stock.id,
                    NewsArticle.published_at >= datetime.now() - timedelta(days=30)
                ).count()
                
                # Validation criteria
                has_sufficient_historical = historical_count >= 252  # At least 1 year
                has_financial_metrics = financial_metrics_count > 0
                has_recent_news = recent_news_count > 0
                
                validation_status = {
                    "stock_exists": True,
                    "historical_data_count": historical_count,
                    "has_sufficient_historical": has_sufficient_historical,
                    "financial_metrics_count": financial_metrics_count,
                    "has_financial_metrics": has_financial_metrics,
                    "recent_news_count": recent_news_count,
                    "has_recent_news": has_recent_news,
                    "overall_valid": has_sufficient_historical and has_financial_metrics
                }
                
                return CollectionResult(
                    success=validation_status["overall_valid"],
                    data=validation_status
                )
                
        except Exception as e:
            logger.error(f"Error in data validation: {e}")
            return CollectionResult(
                success=False,
                data={},
                error=str(e)
            )
    
    async def _arun(self, symbol: str) -> CollectionResult:
        """Async version of data validation"""
        return await asyncio.to_thread(self._run, symbol)

class DataCollectionAgent:
    """LangGraph agent for data collection"""
    
    def __init__(self):
        self.llm = OllamaLLM(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature
        )
        
        self.tools = [
            StockDataCollectionTool(),
            NewsCollectionTool(),
            DataValidationTool()
        ]
        
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Create the data collection workflow graph"""
        workflow = StateGraph(DataCollectionState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("collect_stock_data", self._collect_stock_data_node)
        workflow.add_node("collect_news", self._collect_news_node)
        workflow.add_node("validate_data", self._validate_data_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Add edges
        workflow.add_edge("initialize", "collect_stock_data")
        workflow.add_edge("collect_stock_data", "collect_news")
        workflow.add_edge("collect_news", "validate_data")
        workflow.add_edge("validate_data", "finalize")
        workflow.add_edge("finalize", END)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        return workflow.compile()
    
    def _initialize_node(self, state: DataCollectionState) -> DataCollectionState:
        """Initialize the data collection process"""
        logger.info(f"Initializing data collection for {state['symbol']}")
        
        return {
            **state,
            "status": "initialized",
            "collected_data": {},
            "next_action": "collect_stock_data"
        }
    
    def _collect_stock_data_node(self, state: DataCollectionState) -> DataCollectionState:
        """Collect stock data"""
        logger.info(f"Collecting stock data for {state['symbol']}")
        
        try:
            tool = StockDataCollectionTool()
            result = tool._run(state["symbol"], state["stock_name"])
            
            if result.success:
                state["collected_data"]["stock_data"] = result.data
                state["status"] = "stock_data_collected"
                state["next_action"] = "collect_news"
            else:
                state["status"] = "error"
                state["error"] = result.error
                state["next_action"] = "finalize"
            
        except Exception as e:
            logger.error(f"Error collecting stock data: {e}")
            state["status"] = "error"
            state["error"] = str(e)
            state["next_action"] = "finalize"
        
        return state
    
    def _collect_news_node(self, state: DataCollectionState) -> DataCollectionState:
        """Collect news data"""
        logger.info(f"Collecting news for {state['symbol']}")
        
        try:
            # Run async news collection
            loop = asyncio.get_event_loop()
            news_tool = NewsCollectionTool()
            result = loop.run_until_complete(
                news_tool._arun(state["symbol"], state["stock_name"])
            )
            
            if result.success:
                state["collected_data"]["news_data"] = result.data
                state["status"] = "news_collected"
                state["next_action"] = "validate_data"
            else:
                logger.warning(f"News collection failed: {result.error}")
                # Continue even if news collection fails
                state["collected_data"]["news_data"] = {"error": result.error}
                state["status"] = "news_collection_failed"
                state["next_action"] = "validate_data"
            
        except Exception as e:
            logger.error(f"Error collecting news: {e}")
            state["collected_data"]["news_data"] = {"error": str(e)}
            state["status"] = "news_collection_failed"
            state["next_action"] = "validate_data"
        
        return state
    
    def _validate_data_node(self, state: DataCollectionState) -> DataCollectionState:
        """Validate collected data"""
        logger.info(f"Validating data for {state['symbol']}")
        
        try:
            tool = DataValidationTool()
            result = tool._run(state["symbol"])
            
            state["collected_data"]["validation"] = result.data
            
            if result.success:
                state["status"] = "data_validated"
            else:
                state["status"] = "validation_failed"
                state["error"] = result.error
            
            state["next_action"] = "finalize"
            
        except Exception as e:
            logger.error(f"Error validating data: {e}")
            state["status"] = "validation_error"
            state["error"] = str(e)
            state["next_action"] = "finalize"
        
        return state
    
    def _finalize_node(self, state: DataCollectionState) -> DataCollectionState:
        """Finalize the data collection process"""
        logger.info(f"Finalizing data collection for {state['symbol']}")
        
        # Generate summary
        summary = self._generate_summary(state)
        state["collected_data"]["summary"] = summary
        
        if state["status"] not in ["error", "validation_error"]:
            state["status"] = "completed"
        
        state["next_action"] = "done"
        
        return state
    
    def _generate_summary(self, state: DataCollectionState) -> str:
        """Generate a summary of the data collection process"""
        try:
            collected_data = state["collected_data"]
            
            # Create prompt for LLM
            prompt = f"""You are a data analysis expert. Provide a concise summary of the data collection results.

Analyze the data collection results for stock {state['symbol']} and provide a comprehensive summary.

Stock Data Collection Results:
{collected_data.get('stock_data', {})}

News Collection Results:
{collected_data.get('news_data', {})}

Validation Results:
{collected_data.get('validation', {})}

Status: {state['status']}
Error: {state.get('error', 'None')}

Please provide:
1. Data collection success rate
2. Data quality assessment
3. Any issues encountered
4. Recommendations for further analysis

Summary:"""
            
            response = self.llm.invoke(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Summary generation failed: {str(e)}"
    
    async def collect_data(self, symbol: str, stock_name: str) -> Dict:
        """Main method to collect data for a stock"""
        initial_state = DataCollectionState(
            symbol=symbol.upper(),
            stock_name=stock_name,
            task="data_collection",
            collected_data={},
            status="pending",
            error=None,
            next_action="initialize"
        )
        
        # Run the workflow
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "symbol": final_state["symbol"],
            "status": final_state["status"],
            "collected_data": final_state["collected_data"],
            "error": final_state.get("error")
        }

# Create global instance
data_collection_agent = DataCollectionAgent() 