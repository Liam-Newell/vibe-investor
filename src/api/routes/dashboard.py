"""
Dashboard API Routes
Provides live trading dashboard with real-time position updates
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, List

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

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Main trading dashboard with live data updates
    Shows email content, current positions, and real-time Yahoo Finance data
    """
    try:
        # Initialize services
        options_service = OptionsService()
        portfolio_service = PortfolioService()
        market_service = MarketDataService()
        email_service = EmailService()
        claude_service = ClaudeService()
        
        await options_service.initialize()
        await market_service.initialize()
        
        # Get real-time portfolio data
        portfolio = await options_service.get_portfolio_summary()
        current_positions = await options_service.get_active_positions()
        
        # Get live market data for current positions
        position_symbols = list(set([pos.symbol for pos in current_positions]))
        live_market_data = {}
        
        for symbol in position_symbols:
            try:
                market_data = await market_service.get_market_data(symbol)
                if market_data:
                    live_market_data[symbol] = {
                        "price": market_data.price,
                        "change_pct": market_data.change_pct,
                        "volume": market_data.volume,
                        "timestamp": market_data.timestamp.isoformat()
                    }
            except Exception as e:
                logger.warning(f"Failed to get market data for {symbol}: {e}")
                live_market_data[symbol] = {"error": str(e)}
        
        # Get general market summary
        market_summary = await market_service.get_market_summary()
        
        # Generate email-style content for dashboard
        email_content = await _generate_dashboard_email_content(
            portfolio, current_positions, market_summary, claude_service
        )
        
        # Calculate position P&L with live data
        positions_with_live_data = await _calculate_live_position_pnl(
            current_positions, live_market_data, market_service
        )
        
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
        
        await market_service.close()
        
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
    try:
        # Initialize services
        options_service = OptionsService()
        market_service = MarketDataService()
        
        await options_service.initialize()
        await market_service.initialize()
        
        # Get current data
        portfolio = await options_service.get_portfolio_summary()
        current_positions = await options_service.get_active_positions()
        
        # Update position values with live data
        await options_service.update_position_values()
        
        # Get live market data for positions
        position_symbols = list(set([pos.symbol for pos in current_positions]))
        live_market_data = {}
        
        for symbol in position_symbols:
            try:
                market_data = await market_service.get_market_data(symbol)
                if market_data:
                    live_market_data[symbol] = {
                        "price": market_data.price,
                        "change_pct": market_data.change_pct,
                        "volume": market_data.volume
                    }
            except Exception as e:
                live_market_data[symbol] = {"error": str(e)}
        
        # Get market summary
        market_summary = await market_service.get_market_summary()
        
        # Calculate live position P&L
        positions_with_live_data = await _calculate_live_position_pnl(
            current_positions, live_market_data, market_service
        )
        
        await market_service.close()
        
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
    positions_with_live_data = []
    
    for position in positions:
        try:
            # Get live market data for this symbol
            symbol_data = live_market_data.get(position.symbol, {})
            
            # Calculate live option value if possible
            live_option_value = None
            if not symbol_data.get('error'):
                try:
                    # Use market service to get option pricing
                    for contract in position.contracts:
                        option_price = await market_service.get_option_price(
                            position.symbol,
                            contract.strike_price,
                            contract.expiration_date,
                            contract.option_type
                        )
                        if option_price:
                            # Calculate total position value
                            total_contracts = sum(abs(c.quantity) for c in position.contracts)
                            live_option_value = option_price * total_contracts * 100  # Options are per 100 shares
                            break
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
            
            position_data = {
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
            
            positions_with_live_data.append(position_data)
            
        except Exception as e:
            logger.error(f"❌ Error calculating live P&L for position {position.symbol}: {e}")
            # Add position with error
            positions_with_live_data.append({
                "id": str(position.id),
                "symbol": position.symbol,
                "strategy": position.strategy_type.value,
                "error": str(e),
                "entry_cost": position.entry_cost,
                "unrealized_pnl": position.unrealized_pnl
            })
    
    return positions_with_live_data 