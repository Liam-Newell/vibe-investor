"""
Trading Scheduler
Handles scheduled Claude sessions and position monitoring
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.core.config import settings

logger = logging.getLogger(__name__)

class TradingScheduler:
    """Scheduler for Claude sessions and position monitoring"""
    
    def __init__(self, claude_service, options_service, portfolio_service, email_service=None):
        self.claude_service = claude_service
        self.options_service = options_service
        self.portfolio_service = portfolio_service
        self.email_service = email_service
        self.scheduler = AsyncIOScheduler()
        self._running = False
        
    async def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        self._running = True
        logger.info("⏰ Trading scheduler started")
        
    async def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        self._running = False
        logger.info("⏰ Trading scheduler stopped")
        
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running
        
    async def schedule_morning_session(self):
        """Schedule morning Claude strategy session"""
        if not settings.CLAUDE_MORNING_ENABLED:
            return
            
        hour, minute = map(int, settings.CLAUDE_MORNING_TIME.split(':'))
        
        self.scheduler.add_job(
            self._morning_session,
            CronTrigger(hour=hour, minute=minute, day_of_week='mon-fri'),
            id='morning_session',
            name='Morning Claude Strategy Session'
        )
        
        logger.info(f"📅 Scheduled morning session at {settings.CLAUDE_MORNING_TIME}")
        
    async def schedule_evening_session(self):
        """Schedule evening Claude review session"""
        if not settings.CLAUDE_EVENING_ENABLED:
            return
            
        hour, minute = map(int, settings.CLAUDE_EVENING_TIME.split(':'))
        
        self.scheduler.add_job(
            self._evening_session,
            CronTrigger(hour=hour, minute=minute, day_of_week='mon-fri'),
            id='evening_session',
            name='Evening Claude Review Session'
        )
        
        logger.info(f"📅 Scheduled evening session at {settings.CLAUDE_EVENING_TIME}")
        
    async def _morning_session(self):
        """Execute morning Claude strategy session"""
        try:
            logger.info("🌅 Starting scheduled morning session")
            
            # Get current portfolio and positions
            portfolio = await self.options_service.get_portfolio_summary()
            positions = await self.options_service.get_active_positions()
            
            # Mock market data for now
            market_data = {
                "vix": 20.0, 
                "spy_price": 450.0,
                "market_sentiment": "Neutral",
                "sector_rotation": "Technology leading",
                "volatility_trend": "Elevated but stable"
            }
            earnings_calendar = []
            
            # Run Claude morning session
            opportunities = await self.claude_service.morning_strategy_session(
                portfolio, market_data, earnings_calendar, positions
            )
            
            logger.info(f"🌅 Morning session complete. Found {len(opportunities)} opportunities")
            
            # Send email report
            if self.email_service and opportunities:
                claude_analysis = f"""
                Today's market analysis identified {len(opportunities)} high-probability options opportunities.
                Key market conditions: VIX at {market_data['vix']}, SPY at ${market_data['spy_price']}.
                
                Portfolio currently has {portfolio.open_positions} open positions with 
                ${portfolio.cash_balance:,.2f} available for new trades.
                
                Recommended strategies focus on:
                • {opportunities[0].strategy_type if opportunities else 'Long calls'} on high-conviction picks
                • Risk-defined positions with 2-4 week time horizons
                • Volatility opportunities with favorable risk/reward
                
                All positions will be monitored with individual Claude conversations for optimal management.
                """
                
                await self.email_service.send_morning_report(
                    opportunities=[opp.dict() for opp in opportunities],
                    portfolio=portfolio,
                    market_data=market_data,
                    claude_analysis=claude_analysis
                )
            
        except Exception as e:
            logger.error(f"❌ Morning session failed: {e}")
            
    async def _evening_session(self):
        """Execute evening Claude review session"""
        try:
            logger.info("🌆 Starting scheduled evening session")
            
            # Get current portfolio and positions
            portfolio = await self.options_service.get_portfolio_summary()
            positions = await self.options_service.get_active_positions()
            
            # Mock data for now
            daily_trades = [
                {
                    "time": "10:30 AM",
                    "action": "BUY",
                    "symbol": "AAPL",
                    "strategy": "Long Call",
                    "cost": "$1,200",
                    "reason": "Claude identified bullish momentum"
                }
            ]
            market_summary = {
                "day_change": "+0.5%",
                "volume": "Above average",
                "volatility": "Decreased from morning",
                "sector_performance": "Technology outperformed"
            }
            
            # Run Claude evening session
            review = await self.claude_service.evening_review_session(
                portfolio, positions, daily_trades, market_summary
            )
            
            logger.info("🌆 Evening session complete")
            
            # Get performance metrics
            performance_metrics = await self.portfolio_service.get_performance_metrics(positions)
            
            # Send email report
            if self.email_service:
                await self.email_service.send_evening_report(
                    portfolio=portfolio,
                    positions=positions,
                    daily_trades=daily_trades,
                    performance_metrics=performance_metrics,
                    claude_review=review
                )
            
        except Exception as e:
            logger.error(f"❌ Evening session failed: {e}")
            
    async def schedule_position_monitoring(self):
        """Schedule regular position monitoring"""
        self.scheduler.add_job(
            self._monitor_positions,
            'interval',
            minutes=30,
            id='position_monitoring',
            name='Position Monitoring'
        )
        
        logger.info("📊 Scheduled position monitoring every 30 minutes")
        
    async def _monitor_positions(self):
        """Monitor positions for Claude check-in triggers"""
        try:
            positions = await self.options_service.get_active_positions()
            portfolio = await self.options_service.get_portfolio_summary()
            
            for position in positions:
                if position.should_check_with_claude():
                    logger.info(f"🔍 Position {position.symbol} requires Claude check-in")
                    
                    # Mock market data
                    market_data = {"current_price": 100.0, "volatility": 0.25}
                    
                    # Analyze position with Claude
                    decision = await self.claude_service.analyze_position(
                        position, market_data, portfolio
                    )
                    
                    if decision:
                        logger.info(f"🤖 Claude recommendation for {position.symbol}: {decision.action}")
                        
        except Exception as e:
            logger.error(f"❌ Position monitoring failed: {e}") 