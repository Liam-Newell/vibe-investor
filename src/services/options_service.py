"""
Options Service - Paper Trading Implementation
Handles options execution, Greeks calculation, and position management
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from src.models.options import OptionsPosition, OptionContract, PortfolioSummary
from src.core.config import settings

logger = logging.getLogger(__name__)

class OptionsService:
    """Options trading service with paper trading support"""
    
    def __init__(self):
        self.paper_trading_enabled = settings.PAPER_TRADING_ONLY
        self.positions: Dict[UUID, OptionsPosition] = {}
        self.portfolio_value = 100000.0  # Starting paper trading capital
        self.cash_balance = 100000.0
        
    async def enable_paper_trading(self):
        """Enable paper trading mode"""
        self.paper_trading_enabled = True
        logger.info("📝 Paper trading mode enabled")
    
    async def get_portfolio_summary(self) -> PortfolioSummary:
        """Get current portfolio summary"""
        total_pnl = sum(pos.total_pnl for pos in self.positions.values())
        
        return PortfolioSummary(
            total_value=self.portfolio_value,
            cash_balance=self.cash_balance,
            total_pnl=total_pnl,
            open_positions=len([p for p in self.positions.values() if p.status == "open"]),
            win_rate=0.0,  # Calculate from closed positions
            average_win=0.0,
            average_loss=0.0,
            max_drawdown=0.0
        )
    
    async def get_active_positions(self) -> List[OptionsPosition]:
        """Get all active positions"""
        return [pos for pos in self.positions.values() if pos.status == "open"]
    
    async def create_position(self, position: OptionsPosition) -> bool:
        """Create a new options position (paper trading)"""
        if not self.paper_trading_enabled:
            logger.error("Live trading not implemented yet")
            return False
        
        # Paper trading simulation
        self.positions[position.id] = position
        self.cash_balance -= position.entry_cost
        
        logger.info(f"📝 Paper trade: Created {position.symbol} position for ${position.entry_cost}")
        return True
    
    async def close_position(self, position_id: UUID, exit_price: float) -> bool:
        """Close an options position"""
        if position_id not in self.positions:
            return False
        
        position = self.positions[position_id]
        position.status = "closed"
        position.current_value = exit_price * position.quantity
        position.realized_pnl = position.current_value - position.entry_cost
        
        self.cash_balance += position.current_value
        
        logger.info(f"📝 Paper trade: Closed {position.symbol} position. P&L: ${position.realized_pnl:.2f}")
        return True
    
    async def update_position_values(self):
        """Update current values for all positions (mock data for now)"""
        # This would fetch real market data in production
        for position in self.positions.values():
            if position.status == "open":
                # Mock price movement for paper trading
                import random
                change_pct = random.uniform(-0.05, 0.05)  # ±5% daily change
                position.current_value = position.entry_cost * (1 + change_pct)
                position.unrealized_pnl = position.current_value - position.entry_cost
        
        logger.debug("📊 Updated position values (mock data)")
    
    def get_position(self, position_id: UUID) -> Optional[OptionsPosition]:
        """Get a specific position"""
        return self.positions.get(position_id) 