"""
Portfolio Service
Handles portfolio-wide risk management, metrics, and dynamic confidence calculations
"""

import logging
from typing import List, Dict, Any
from src.models.options import PortfolioSummary, OptionsPosition, StrategyType
from src.core.config import settings

logger = logging.getLogger(__name__)

class PortfolioService:
    """Portfolio management, risk monitoring, and dynamic confidence calculation service"""
    
    def __init__(self):
        self.risk_limits = {
            "max_delta": settings.MAX_PORTFOLIO_DELTA,
            "max_vega": settings.MAX_PORTFOLIO_VEGA,
            "max_theta": settings.MAX_PORTFOLIO_THETA,
            "max_daily_loss": settings.MAX_DAILY_LOSS_PCT,
            "max_position_size": settings.MAX_POSITION_SIZE_PCT,
        }
        
        # Strategy-specific base confidence thresholds (research-based)
        self.base_confidence_thresholds = {
            StrategyType.LONG_PUT: settings.MIN_CONFIDENCE_LONG_PUTS,
            StrategyType.LONG_CALL: settings.MIN_CONFIDENCE_LONG_CALLS,
            StrategyType.CALL_SPREAD: settings.MIN_CONFIDENCE_CREDIT_SPREADS,
            StrategyType.PUT_SPREAD: settings.MIN_CONFIDENCE_PUT_SPREADS,
            StrategyType.IRON_CONDOR: settings.MIN_CONFIDENCE_IRON_CONDORS,
            StrategyType.STRADDLE: settings.MIN_CONFIDENCE_CREDIT_SPREADS,  # Similar to credit spreads
            StrategyType.STRANGLE: settings.MIN_CONFIDENCE_CREDIT_SPREADS,
            StrategyType.COVERED_CALL: settings.MIN_CONFIDENCE_CREDIT_SPREADS,
            StrategyType.PROTECTIVE_PUT: settings.MIN_CONFIDENCE_LONG_PUTS,
        }
    
    def calculate_dynamic_confidence_threshold(self, strategy_type: StrategyType, portfolio: PortfolioSummary) -> float:
        """
        Calculate dynamic confidence threshold based on strategy type and current performance
        
        Research-based approach:
        - Long puts need 78%+ confidence (volatility risk)
        - Credit spreads need 68%+ confidence (defined risk) 
        - Iron condors need 65%+ confidence (market neutral)
        - Adjusts based on recent performance streaks
        """
        # Start with research-based base threshold
        base_threshold = self.base_confidence_thresholds.get(strategy_type, 0.70)
        
        # Get current performance metrics
        current_streak = portfolio.performance_history.current_streak
        consecutive_losses = portfolio.performance_history.consecutive_losses
        recent_win_rate = portfolio.performance_history.recent_win_rate
        
        # Performance-based adjustments
        adjustment = 0.0
        
        # Increase threshold after losses (be more cautious)
        if consecutive_losses >= 3:
            adjustment += settings.CONFIDENCE_BOOST_AFTER_LOSSES * 1.5  # 15% boost
            logger.info(f"💡 Increasing confidence threshold by {adjustment:.1%} after {consecutive_losses} consecutive losses")
        elif consecutive_losses >= 2:
            adjustment += settings.CONFIDENCE_BOOST_AFTER_LOSSES  # 10% boost
            logger.info(f"💡 Increasing confidence threshold by {adjustment:.1%} after {consecutive_losses} consecutive losses")
        
        # Slightly decrease threshold after wins (be more aggressive)
        elif current_streak >= 4:
            adjustment -= settings.CONFIDENCE_REDUCTION_AFTER_WINS  # 5% reduction
            logger.info(f"🔥 Decreasing confidence threshold by {adjustment:.1%} after {current_streak} consecutive wins")
        
        # Additional adjustment based on recent win rate
        if recent_win_rate < 50.0:  # Poor recent performance
            adjustment += 0.05  # Extra 5% boost
            logger.info(f"⚠️ Poor recent win rate ({recent_win_rate:.1f}%), adding extra 5% confidence boost")
        elif recent_win_rate > 80.0:  # Excellent recent performance
            adjustment -= 0.03  # Small 3% reduction
            logger.info(f"✅ Excellent recent win rate ({recent_win_rate:.1f}%), reducing confidence threshold by 3%")
        
        # Calculate final threshold with bounds
        final_threshold = base_threshold + adjustment
        final_threshold = max(settings.MIN_CONFIDENCE_FLOOR, min(settings.MAX_CONFIDENCE_CEILING, final_threshold))
        
        logger.info(f"📊 Dynamic confidence for {strategy_type.value}: {final_threshold:.1%} (base: {base_threshold:.1%}, adjustment: {adjustment:+.1%})")
        
        return final_threshold
    
    def should_execute_opportunity(self, opportunity: Dict[str, Any], portfolio: PortfolioSummary) -> bool:
        """
        Determine if an opportunity meets dynamic confidence thresholds and risk criteria
        """
        strategy_type = StrategyType(opportunity.get('strategy_type', 'long_call'))
        confidence = opportunity.get('confidence', 0.0)
        
        # Get dynamic threshold for this strategy
        required_confidence = self.calculate_dynamic_confidence_threshold(strategy_type, portfolio)
        
        # Check confidence threshold
        if confidence < required_confidence:
            logger.info(f"❌ {opportunity.get('symbol')} {strategy_type.value} rejected: {confidence:.1%} < {required_confidence:.1%} required")
            return False
        
        # Check cash reserve requirements
        if portfolio.cash_balance < settings.MIN_CASH_RESERVE_FOR_TRADES:
            logger.warning(f"❌ Insufficient cash reserve: ${portfolio.cash_balance:,.0f} < ${settings.MIN_CASH_RESERVE_FOR_TRADES:,.0f} required")
            return False
        
        # Check position limits
        if portfolio.open_positions >= settings.MAX_SWING_POSITIONS:
            logger.warning(f"❌ Maximum positions reached: {portfolio.open_positions}/{settings.MAX_SWING_POSITIONS}")
            return False
        
        logger.info(f"✅ {opportunity.get('symbol')} {strategy_type.value} approved: {confidence:.1%} confidence meets {required_confidence:.1%} threshold")
        return True
    
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