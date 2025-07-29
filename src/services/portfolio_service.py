"""
Portfolio Service
Handles portfolio-wide risk management and metrics
"""

import logging
from typing import List, Dict, Any

from src.models.options import PortfolioSummary, OptionsPosition
from src.core.config import settings

logger = logging.getLogger(__name__)

class PortfolioService:
    """Portfolio management and risk monitoring service"""
    
    def __init__(self):
        self.risk_limits = {
            "max_delta": settings.MAX_PORTFOLIO_DELTA,
            "max_vega": settings.MAX_PORTFOLIO_VEGA,
            "max_theta": settings.MAX_PORTFOLIO_THETA,
            "max_daily_loss": settings.MAX_DAILY_LOSS_PCT,
            "max_position_size": settings.MAX_POSITION_SIZE_PCT,
        }
        
    async def calculate_portfolio_greeks(self, positions: List[OptionsPosition]) -> Dict[str, float]:
        """Calculate portfolio-wide Greeks"""
        total_delta = sum(pos.portfolio_delta for pos in positions if pos.status == "open")
        total_gamma = sum(pos.portfolio_gamma for pos in positions if pos.status == "open")
        total_theta = sum(pos.portfolio_theta for pos in positions if pos.status == "open")
        total_vega = sum(pos.portfolio_vega for pos in positions if pos.status == "open")
        
        return {
            "delta": total_delta,
            "gamma": total_gamma,
            "theta": total_theta,
            "vega": total_vega
        }
    
    async def check_risk_limits(self, positions: List[OptionsPosition]) -> List[str]:
        """Check portfolio against risk limits"""
        warnings = []
        greeks = await self.calculate_portfolio_greeks(positions)
        
        if abs(greeks["delta"]) > self.risk_limits["max_delta"]:
            warnings.append(f"Portfolio delta ({greeks['delta']:.2f}) exceeds limit ({self.risk_limits['max_delta']})")
        
        if abs(greeks["vega"]) > self.risk_limits["max_vega"]:
            warnings.append(f"Portfolio vega ({greeks['vega']:.2f}) exceeds limit ({self.risk_limits['max_vega']})")
        
        return warnings
    
    async def get_performance_metrics(self, positions: List[OptionsPosition]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        closed_positions = [p for p in positions if p.status == "closed"]
        
        if not closed_positions:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "profit_factor": 0.0
            }
        
        winning_trades = [p for p in closed_positions if p.realized_pnl > 0]
        losing_trades = [p for p in closed_positions if p.realized_pnl < 0]
        
        win_rate = len(winning_trades) / len(closed_positions) * 100
        avg_win = sum(p.realized_pnl for p in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(p.realized_pnl for p in losing_trades) / len(losing_trades) if losing_trades else 0
        
        total_wins = sum(p.realized_pnl for p in winning_trades)
        total_losses = abs(sum(p.realized_pnl for p in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        return {
            "total_trades": len(closed_positions),
            "win_rate": win_rate,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "profit_factor": profit_factor
        } 