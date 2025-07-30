"""
Dashboard API Routes
Provides live trading dashboard with real-time position updates
"""

import logging
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List, Optional
import time

from src.services.claude_service import ClaudeService
from src.services.options_service import OptionsService
from src.services.portfolio_service import PortfolioService
from src.services.market_data_service import MarketDataService
from src.services.email_service import EmailService
from src.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Service cache to avoid reinitializing on every request
_service_cache = {
    "options_service": None,
    "market_service": None,
    "portfolio_service": None,
    "email_service": None,
    "claude_service": None,
    "last_initialized": None
}

# Market data cache (30 second TTL)
_market_data_cache = {}
_cache_ttl = 30  # seconds

async def get_cached_services():
    """Get cached services or initialize them if needed"""
    global _service_cache
    
    # Re-initialize services every 5 minutes to prevent stale connections
    if (_service_cache["last_initialized"] is None or 
        (datetime.now() - _service_cache["last_initialized"]).seconds > 300):
        
        logger.info("♻️ Initializing fresh services...")
        
        # Initialize all services in parallel
        tasks = []
        
        options_service = OptionsService()
        tasks.append(options_service.initialize())
        
        market_service = MarketDataService() 
        tasks.append(market_service.initialize())
        
        # Run parallel initialization
        await asyncio.gather(*tasks, return_exceptions=True)
        
        _service_cache.update({
            "options_service": options_service,
            "market_service": market_service,
            "portfolio_service": PortfolioService(),
            "email_service": EmailService(),
            "claude_service": ClaudeService(),
            "last_initialized": datetime.now()
        })
        
        logger.info("✅ Services initialized in parallel")
    
    return _service_cache

async def get_cached_market_data(symbol: str, market_service) -> Optional[Dict]:
    """Get market data with caching"""
    global _market_data_cache
    
    cache_key = f"market_data_{symbol}"
    now = time.time()
    
    # Check if we have fresh cached data
    if cache_key in _market_data_cache:
        cached_data, timestamp = _market_data_cache[cache_key]
        if now - timestamp < _cache_ttl:
            return cached_data
    
    # Fetch fresh data
    try:
        market_data = await market_service.get_market_data(symbol)
        if market_data:
            result = {
                "price": market_data.price,
                "change_pct": market_data.change_pct,
                "volume": market_data.volume,
                "timestamp": market_data.timestamp.isoformat()
            }
            _market_data_cache[cache_key] = (result, now)
            return result
    except Exception as e:
        logger.warning(f"Failed to get market data for {symbol}: {e}")
        return {"error": str(e)}
    
    return None

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Main trading dashboard with live data updates
    Shows email content, current positions, and real-time Yahoo Finance data
    """
    start_time = time.time()
    
    try:
        # Get cached services (much faster than reinitializing)
        services = await get_cached_services()
        options_service = services["options_service"]
        portfolio_service = services["portfolio_service"]
        market_service = services["market_service"]
        email_service = services["email_service"]
        claude_service = services["claude_service"]
        
        logger.info("📊 Loading dashboard data...")
        
        # Parallel data fetching for better performance
        portfolio_task = options_service.get_portfolio_summary()
        positions_task = options_service.get_active_positions()
        market_summary_task = market_service.get_market_summary()
        
        # Execute core data fetching in parallel
        portfolio, current_positions, market_summary = await asyncio.gather(
            portfolio_task,
            positions_task, 
            market_summary_task,
            return_exceptions=True
        )
        
        # Handle any exceptions from parallel execution
        if isinstance(portfolio, Exception):
            logger.error(f"Portfolio fetch error: {portfolio}")
            portfolio = await _get_default_portfolio()
        if isinstance(current_positions, Exception):
            logger.error(f"Positions fetch error: {current_positions}")
            current_positions = []
        if isinstance(market_summary, Exception):
            logger.error(f"Market summary fetch error: {market_summary}")
            market_summary = {}
        
        # Get live market data for positions in parallel
        position_symbols = list(set([pos.symbol for pos in current_positions]))
        live_market_data = {}
        
        if position_symbols:
            # Parallel market data fetching for all symbols
            market_data_tasks = [
                get_cached_market_data(symbol, market_service) 
                for symbol in position_symbols
            ]
            
            market_data_results = await asyncio.gather(
                *market_data_tasks, 
                return_exceptions=True
            )
            
            # Combine results
            for symbol, result in zip(position_symbols, market_data_results):
                if isinstance(result, Exception):
                    live_market_data[symbol] = {"error": str(result)}
                else:
                    live_market_data[symbol] = result or {"error": "No data"}
        
        # Generate content and calculate P&L in parallel
        email_content_task = _generate_dashboard_email_content(
            portfolio, current_positions, market_summary, claude_service
        )
        
        positions_pnl_task = _calculate_live_position_pnl(
            current_positions, live_market_data, market_service
        )
        
        email_content, positions_with_live_data = await asyncio.gather(
            email_content_task,
            positions_pnl_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(email_content, Exception):
            logger.error(f"Email content error: {email_content}")
            email_content = {"morning": "Error loading content", "evening": "Error loading content"}
        if isinstance(positions_with_live_data, Exception):
            logger.error(f"Position P&L error: {positions_with_live_data}")
            positions_with_live_data = []
        
        # Prepare dashboard data
        dashboard_data = {
            "timestamp": datetime.now(),
            "portfolio": {
                "total_value": portfolio.total_value,
                "cash_balance": portfolio.cash_balance,
                "total_pnl": portfolio.total_pnl,
                "open_positions": portfolio.open_positions,
                "win_rate": portfolio.win_rate,
                "current_streak": portfolio.performance_history.current_streak,
                "recent_win_rate": portfolio.performance_history.recent_win_rate,
                "risk_level": portfolio.get_adaptive_risk_level(),
                "last_7_days_pnl": portfolio.performance_history.last_7_days_pnl,
                "last_30_days_pnl": portfolio.performance_history.last_30_days_pnl
            },
            "market_summary": market_summary,
            "positions": positions_with_live_data,
            "email_content": email_content,
            "auto_trading_enabled": settings.AUTO_EXECUTE_TRADES,
            "paper_trading": settings.PAPER_TRADING_ONLY,
            "max_positions": settings.MAX_SWING_POSITIONS
        }
        
        # Don't close cached services
        
        load_time = time.time() - start_time
        logger.info(f"📊 Dashboard loaded in {load_time:.2f}s")
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "data": dashboard_data
        })
        
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        error_data = {
            "timestamp": datetime.now(),
            "error": str(e),
            "portfolio": {"total_value": 0, "cash_balance": 0, "total_pnl": 0, "open_positions": 0},
            "positions": [],
            "email_content": {"morning": "Error loading content", "evening": "Error loading content"}
        }
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "data": error_data
        })

@router.get("/api/live-update")
async def get_live_update():
    """
    API endpoint for live data updates (for AJAX refresh)
    Returns JSON data for dashboard updates
    """
    start_time = time.time()
    
    try:
        # Use cached services for much faster response
        services = await get_cached_services()
        options_service = services["options_service"]
        market_service = services["market_service"]
        
        # Get current data in parallel
        portfolio_task = options_service.get_portfolio_summary()
        positions_task = options_service.get_active_positions()
        market_summary_task = market_service.get_market_summary()
        update_values_task = options_service.update_position_values()
        
        # Execute in parallel
        portfolio, current_positions, market_summary, _ = await asyncio.gather(
            portfolio_task,
            positions_task,
            market_summary_task, 
            update_values_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(portfolio, Exception):
            portfolio = await _get_default_portfolio()
        if isinstance(current_positions, Exception):
            current_positions = []
        if isinstance(market_summary, Exception):
            market_summary = {}
        
        # Get live market data for positions in parallel (cached)
        position_symbols = list(set([pos.symbol for pos in current_positions]))
        live_market_data = {}
        
        if position_symbols:
            # Parallel market data fetching with caching
            market_data_tasks = [
                get_cached_market_data(symbol, market_service) 
                for symbol in position_symbols
            ]
            
            market_data_results = await asyncio.gather(
                *market_data_tasks, 
                return_exceptions=True
            )
            
            # Combine results
            for symbol, result in zip(position_symbols, market_data_results):
                if isinstance(result, Exception):
                    live_market_data[symbol] = {"error": str(result)}
                else:
                    live_market_data[symbol] = result or {"error": "No data"}
        
        # Calculate live position P&L in parallel
        positions_with_live_data = await _calculate_live_position_pnl(
            current_positions, live_market_data, market_service
        )
        
        # Don't close cached services
        
        load_time = time.time() - start_time
        logger.debug(f"📡 Live update completed in {load_time:.2f}s")
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "portfolio": {
                "total_value": portfolio.total_value,
                "cash_balance": portfolio.cash_balance,
                "total_pnl": portfolio.total_pnl,
                "open_positions": portfolio.open_positions
            },
            "market_summary": market_summary,
            "positions": positions_with_live_data,
            "live_market_data": live_market_data
        }
        
    except Exception as e:
        logger.error(f"❌ Live update error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def _generate_dashboard_email_content(portfolio, positions, market_data, claude_service) -> Dict[str, str]:
    """Generate email-style content for dashboard display"""
    try:
        # Simulate morning email content
        morning_content = f"""
        <div class="email-section">
            <h3>🌅 Morning Trading Report</h3>
            <p><strong>Market Status:</strong> {market_data.get('market_sentiment', 'Unknown')}</p>
            <p><strong>SPY:</strong> ${market_data.get('spy_price', 'N/A')} ({market_data.get('spy_change', 0):+.2f}%)</p>
            <p><strong>VIX:</strong> {market_data.get('vix', 'N/A')} ({market_data.get('vix_change', 0):+.2f}%)</p>
            <p><strong>Portfolio Performance:</strong> {portfolio.performance_history.current_streak} current streak</p>
            <p><strong>Risk Level:</strong> {portfolio.get_adaptive_risk_level()}</p>
            <p><strong>Available Cash:</strong> ${portfolio.cash_balance:,.0f}</p>
            <p><strong>Open Positions:</strong> {portfolio.open_positions}/{settings.MAX_SWING_POSITIONS}</p>
        </div>
        """
        
        # Simulate evening email content with positions
        evening_content = f"""
        <div class="email-section">
            <h3>🌆 Evening Performance Report</h3>
            <p><strong>Total Portfolio Value:</strong> ${portfolio.total_value:,.0f}</p>
            <p><strong>Total P&L:</strong> ${portfolio.total_pnl:,.0f}</p>
            <p><strong>Win Rate:</strong> {portfolio.win_rate:.1%}</p>
            <p><strong>Recent Win Rate:</strong> {portfolio.performance_history.recent_win_rate:.1%}</p>
            <p><strong>Last 7 Days P&L:</strong> ${portfolio.performance_history.last_7_days_pnl:,.0f}</p>
            <p><strong>Last 30 Days P&L:</strong> ${portfolio.performance_history.last_30_days_pnl:,.0f}</p>
        </div>
        """
        
        return {
            "morning": morning_content,
            "evening": evening_content
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating email content: {e}")
        return {
            "morning": f"Error generating morning content: {e}",
            "evening": f"Error generating evening content: {e}"
        }

async def _calculate_live_position_pnl(positions, live_market_data, market_service) -> List[Dict]:
    """Calculate live P&L for positions using Yahoo Finance data"""
    if not positions:
        return []
    
    # Process positions in parallel for better performance
    tasks = []
    for position in positions:
        tasks.append(_process_single_position(position, live_market_data, market_service))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and return valid results
    positions_with_live_data = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"❌ Error processing position {positions[i].symbol}: {result}")
            # Add error position
            positions_with_live_data.append({
                "id": str(positions[i].id),
                "symbol": positions[i].symbol,
                "strategy": positions[i].strategy_type.value,
                "error": str(result),
                "entry_cost": positions[i].entry_cost,
                "unrealized_pnl": positions[i].unrealized_pnl
            })
        else:
            positions_with_live_data.append(result)
    
    return positions_with_live_data

async def _process_single_position(position, live_market_data, market_service) -> Dict:
    """Process a single position with live data"""
    # Get live market data for this symbol
    symbol_data = live_market_data.get(position.symbol, {})
    
    # Calculate live option value if possible (simplified for performance)
    live_option_value = None
    if not symbol_data.get('error') and position.contracts:
        try:
            # Use a simplified approach - get one option price as representative
            first_contract = position.contracts[0]
            option_price = await market_service.get_option_price(
                position.symbol,
                first_contract.strike_price,
                first_contract.expiration_date,
                first_contract.option_type
            )
            if option_price:
                # Calculate total position value
                total_contracts = sum(abs(c.quantity) for c in position.contracts)
                live_option_value = option_price * total_contracts * 100  # Options are per 100 shares
        except Exception as e:
            logger.warning(f"Failed to get live option price for {position.symbol}: {e}")
    
    # Calculate live P&L
    live_pnl = position.unrealized_pnl
    if live_option_value and position.entry_cost:
        live_pnl = live_option_value - position.entry_cost
    
    # Days held
    days_held = (datetime.now() - position.entry_date).days if hasattr(position, 'entry_date') else 0
    
    # Days to expiry (shortest contract)
    days_to_expiry = min(
        (contract.expiration_date - datetime.now()).days 
        for contract in position.contracts
    ) if position.contracts else 0
    
    return {
        "id": str(position.id),
        "symbol": position.symbol,
        "strategy": position.strategy_type.value,
        "entry_cost": position.entry_cost,
        "current_value": live_option_value or position.current_value,
        "unrealized_pnl": live_pnl,
        "pnl_percentage": (live_pnl / position.entry_cost * 100) if position.entry_cost else 0,
        "days_held": days_held,
        "days_to_expiry": days_to_expiry,
        "live_market_data": symbol_data,
        "entry_date": position.entry_date.isoformat() if hasattr(position, 'entry_date') else None,
        "profit_target": position.profit_target,
        "max_loss": position.max_loss,
        "contracts_count": len(position.contracts),
        "portfolio_delta": position.portfolio_delta,
        "portfolio_theta": position.portfolio_theta
    }

async def _get_default_portfolio():
    """Return a default portfolio in case of errors"""
    from src.models.options import PortfolioSummary, PerformanceHistory
    
    return PortfolioSummary(
        total_value=100000.0,
        cash_balance=100000.0,
        total_pnl=0.0,
        open_positions=0,
        win_rate=0.0,
        average_win=0.0,
        average_loss=0.0,
        max_drawdown=0.0,
        total_delta=0.0,
        total_gamma=0.0,
        total_theta=0.0,
        total_vega=0.0,
        performance_history=PerformanceHistory(
            last_7_days_pnl=0.0,
            last_30_days_pnl=0.0,
            last_60_days_pnl=0.0,
            current_streak=0,
            consecutive_losses=0,
            days_since_last_win=0,
            recent_win_rate=0.0,
            performance_trend="stable",
            risk_confidence=0.5,
            strategy_performance={}
        )
    ) 