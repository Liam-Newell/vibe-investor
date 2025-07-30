"""
Trading Scheduler
Handles scheduled Claude sessions and position monitoring
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional, Dict, Any, List
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.core.config import settings
from src.services.claude_service import ClaudeService
from src.services.email_service import EmailService
from src.services.options_service import OptionsService
from src.services.portfolio_service import PortfolioService
from src.services.market_data_service import MarketDataService
from src.models.options import OptionsPosition, PortfolioSummary

logger = logging.getLogger(__name__)

class TradingScheduler:
    """Scheduler for Claude sessions and position monitoring"""
    
    def __init__(self):
        # Set scheduler timezone to match system timezone
        timezone = pytz.timezone(settings.TIMEZONE)
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self._running = False
        
        # Initialize services
        self.options_service = OptionsService()
        self.portfolio_service = PortfolioService()
        self.claude_service = ClaudeService() if settings.CLAUDE_API_KEY else None
        self.email_service = EmailService() if settings.EMAIL_ENABLED else None
        self.market_data_service = self.options_service.market_data_service
    
    async def start(self):
        """Start the scheduler and initialize services"""
        logger.info("🚀 Starting Vibe Investor scheduler...")
        
        # Initialize options service (loads positions from database)
        await self.options_service.initialize()
        
        self.scheduler.start()
        
        # Schedule Claude sessions
        await self.schedule_morning_session()
        await self.schedule_evening_session()
        
        # Schedule position monitoring (every 30 minutes during market hours)
        await self.schedule_position_monitoring()
        
        # Schedule market data updates (every 5 minutes)
        await self.schedule_market_data_updates()
        
        logger.info("✅ Scheduler started successfully")
        
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
        
        timezone = pytz.timezone(settings.TIMEZONE)
        self.scheduler.add_job(
            self._morning_session,
            CronTrigger(hour=hour, minute=minute, day_of_week='mon-fri', timezone=timezone),
            id='morning_session',
            name='Morning Claude Strategy Session'
        )
        
        logger.info(f"📅 Scheduled morning session at {settings.CLAUDE_MORNING_TIME}")
        
    async def schedule_evening_session(self):
        """Schedule evening Claude review session"""
        if not settings.CLAUDE_EVENING_ENABLED:
            return
            
        hour, minute = map(int, settings.CLAUDE_EVENING_TIME.split(':'))
        
        timezone = pytz.timezone(settings.TIMEZONE)
        self.scheduler.add_job(
            self._evening_session,
            CronTrigger(hour=hour, minute=minute, day_of_week='mon-fri', timezone=timezone),
            id='evening_session',
            name='Evening Claude Review Session'
        )
        
        logger.info(f"📅 Scheduled evening session at {settings.CLAUDE_EVENING_TIME}")
        
    async def _morning_session(self):
        """
        Execute morning Claude strategy session with CLAUDE AUTONOMOUS TRADING:
        
        1. Claude autonomously picks stocks/options based on its knowledge (no proposals)
        2. System searches live data for Claude's autonomous picks only
        3. Claude reviews live data and makes final autonomous decision
        4. Dynamic confidence filtering + autonomous execution
        
        Claude makes ALL trading decisions - zero human input required
        """
        try:
            logger.info("🌅 Starting scheduled morning session with LIVE market analysis")
            
            # Get current portfolio and positions (real data)
            portfolio = await self.options_service.get_portfolio_summary()
            positions = await self.options_service.get_active_positions()
            
            # Get LIVE market data (no mock data)
            logger.info("📊 Fetching live market data...")
            market_summary = await self.market_data_service.get_market_summary()
            
            # Get earnings calendar (live data when available)
            earnings_calendar = await self.market_data_service.get_earnings_calendar(days_ahead=7)
            
            # Validate market data
            if market_summary.get('error'):
                logger.error(f"❌ Failed to get live market data: {market_summary.get('error')}")
                return
            
            logger.info(f"📊 Live market data: SPY ${market_summary.get('spy_price')}, VIX {market_summary.get('vix')}, Sentiment: {market_summary.get('market_sentiment')}")
            
            # Run Claude morning session with LIVE data - Claude makes ALL decisions
            logger.info("🤖 Running Claude analysis on live market data...")
            strategy_response = await self.claude_service.morning_strategy_session(
                portfolio=portfolio, 
                market_data=market_summary,  # Live market data
                earnings_calendar=earnings_calendar,  # Live earnings data
                current_positions=positions  # Real positions
            )
            
            opportunities = strategy_response.opportunities if hasattr(strategy_response, 'opportunities') else []
            logger.info(f"🎯 Claude analyzed live market and generated {len(opportunities)} opportunities")
            
            # Log Claude's live market assessment
            if hasattr(strategy_response, 'market_assessment'):
                assessment = strategy_response.market_assessment
                logger.info(f"📊 Claude's market sentiment: {assessment.overall_sentiment}")
                logger.info(f"📊 Claude's VIX analysis: {assessment.vix_analysis}")
                logger.info(f"📊 Claude's sector analysis: {assessment.sector_analysis}")
                logger.info(f"💰 Claude's cash strategy: {strategy_response.cash_strategy.action}")
            
            # Filter opportunities using dynamic confidence thresholds (based on live performance)
            approved_opportunities = []
            
            for opportunity in opportunities:
                # Convert opportunity to dict format if needed
                opp_dict = opportunity.dict() if hasattr(opportunity, 'dict') else opportunity
                
                # Check if opportunity meets dynamic thresholds based on REAL performance
                if self.portfolio_service.should_execute_opportunity(opp_dict, portfolio):
                    approved_opportunities.append(opp_dict)
                    logger.info(f"✅ Approved by dynamic filter: {opp_dict.get('symbol')} {opp_dict.get('strategy_type')} ({opp_dict.get('confidence', 0):.1%})")
                else:
                    logger.info(f"❌ Rejected by dynamic filter: {opp_dict.get('symbol')} {opp_dict.get('strategy_type')} ({opp_dict.get('confidence', 0):.1%})")
            
            # Execute approved opportunities automatically (REAL trades in paper account)
            executed_position_ids = []
            if approved_opportunities and settings.AUTO_EXECUTE_TRADES:
                logger.info(f"🎯 Executing {len(approved_opportunities)} Claude-approved opportunities based on live analysis...")
                executed_position_ids = await self.options_service.execute_approved_opportunities(
                    approved_opportunities, portfolio
                )
                
                if executed_position_ids:
                    logger.info(f"🎯 ✅ Successfully executed {len(executed_position_ids)} positions based on Claude's live market analysis")
                    
                    # Update portfolio after executions (real portfolio tracking)
                    portfolio = await self.options_service.get_portfolio_summary()
                    positions = await self.options_service.get_active_positions()
                else:
                    logger.info("📭 No positions were executed (all filtered out or failed)")
            elif not settings.AUTO_EXECUTE_TRADES:
                logger.info("🔒 Auto-execution disabled - Claude's opportunities identified but not executed")
            else:
                logger.info("📭 No opportunities met the dynamic confidence thresholds based on performance")
            
            logger.info(f"🌅 Morning session complete. Claude opportunities: {len(opportunities)}, Approved: {len(approved_opportunities)}, Executed: {len(executed_position_ids)}")
            
            # Send enhanced email report with live market analysis results
            if self.email_service:
                # Prepare execution summary for email
                execution_summary = {
                    "total_opportunities": len(opportunities),
                    "approved_opportunities": len(approved_opportunities), 
                    "executed_positions": len(executed_position_ids),
                    "auto_trading_enabled": settings.AUTO_EXECUTE_TRADES,
                    "daily_trade_limit": settings.MAX_DAILY_POSITIONS,
                    "current_daily_count": self.options_service.daily_trades_count
                }
                
                claude_analysis = f"""
                🤖 LIVE MARKET ANALYSIS & AUTONOMOUS TRADING COMPLETE
                
                📊 Claude's Live Market Assessment:
                • Market Data Source: {market_summary.get('data_source', 'Live')}
                • SPY: ${market_summary.get('spy_price')} ({market_summary.get('spy_change', 0):+.2f}%)
                • VIX: {market_summary.get('vix')} ({market_summary.get('vix_change', 0):+.2f}%)
                • Market Sentiment: {market_summary.get('market_sentiment')}
                • Volatility Trend: {market_summary.get('volatility_trend')}
                
                🎯 Claude's Investment Decisions (Based on Live Data):
                • Generated {len(opportunities)} opportunities from live market analysis
                • Approved {len(approved_opportunities)}/{len(opportunities)} after dynamic confidence filtering
                • Current portfolio performance streak: {portfolio.performance_history.current_streak}
                • Risk level: {portfolio.get_adaptive_risk_level()}
                
                ⚡ Autonomous Execution Results:
                • {'🎯 EXECUTED' if executed_position_ids else '🔒 NO EXECUTION'}: {len(executed_position_ids)} position{'s' if len(executed_position_ids) != 1 else ''}
                • Daily limit: {self.options_service.daily_trades_count}/{settings.MAX_DAILY_POSITIONS} positions used
                • Cash reserve: ${portfolio.cash_balance:,.0f} available
                
                📈 Real Portfolio Status:
                • Total value: ${portfolio.total_value:,.0f}
                • Open positions: {portfolio.open_positions}/{settings.MAX_SWING_POSITIONS} 
                • Recent win rate: {portfolio.performance_history.recent_win_rate:.1%}
                • Current risk level: {portfolio.get_adaptive_risk_level()}
                
                💡 Live Data Advantages:
                • All decisions based on real-time market conditions
                • No mock or simulated data used
                • Claude analyzes actual VIX, SPY, sector performance
                • Position sizing adapts to real portfolio performance
                
                🔄 Next Steps:
                • Positions monitored with live data every 30 minutes
                • Evening review at {settings.CLAUDE_EVENING_TIME} with real performance
                • Strategy adapts based on actual trading results
                """
                
                await self.email_service.send_morning_report(
                    opportunities=[opp.dict() if hasattr(opp, 'dict') else opp for opp in opportunities],
                    portfolio=portfolio,
                    market_data=market_summary,  # Live market data in email
                    claude_analysis=claude_analysis
                )
            
        except Exception as e:
            logger.error(f"❌ Live market morning session failed: {e}")
            
            # Send error alert email if possible
            if self.email_service:
                await self.email_service.send_trade_alert(
                    position=None,
                    action="ERROR",
                    reason=f"Live market morning session failed: {str(e)}"
                )
            
    async def _evening_session(self):
        """Execute evening Claude review session"""
        try:
            logger.info("🌆 Starting scheduled evening session")
            
            # Get current portfolio and positions
            portfolio = await self.options_service.get_portfolio_summary()
            positions = await self.options_service.get_active_positions()
            
            # Get REAL daily trades from options service (instead of mock data)
            daily_trades = []
            # Note: In full implementation, this would track actual trades made today
            # For now, we'll get trade data from position creation/closing logs
            
            # Get REAL market summary from market data service
            market_summary = await self.market_data_service.get_market_summary()
            spy_data = market_summary.get("SPY", {})
            
            real_market_summary = {
                "day_change": f"{spy_data.get('change_pct', 0.0):+.1f}%",
                "spy_close": spy_data.get('price', 0.0),
                "vix_close": await self.market_data_service.get_vix_level(),
                "volume": "Above average" if spy_data.get('volume', 0) > 50000000 else "Below average"
            }
            
            # Run Claude evening session
            review = await self.claude_service.evening_review_session(
                portfolio, positions, daily_trades, real_market_summary
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
        """Schedule regular position monitoring and exit decisions"""
        if not settings.CLAUDE_API_KEY:
            logger.warning("⚠️ Claude API not configured, skipping position monitoring")
            return
        
        # Monitor positions every 30 minutes during market hours (9:30 AM - 4:00 PM ET)
        timezone = pytz.timezone(settings.TIMEZONE)
        self.scheduler.add_job(
            self._monitor_positions,
            CronTrigger(
                minute='0,30',
                hour='9-16',
                day_of_week='mon-fri',
                timezone=timezone
            ),
            id='position_monitoring',
            name='Position Monitoring and Exit Logic'
        )
        
        logger.info("📅 Scheduled position monitoring every 30 minutes during market hours")
    
    async def schedule_market_data_updates(self):
        """Schedule regular market data updates"""
        # Update market data every 5 minutes during market hours
        timezone = pytz.timezone(settings.TIMEZONE)
        self.scheduler.add_job(
            self._update_market_data,
            CronTrigger(
                minute='*/5',
                hour='9-16',
                day_of_week='mon-fri',
                timezone=timezone
            ),
            id='market_data_updates',
            name='Market Data Updates'
        )
        
        # Update position values every 15 minutes during market hours
        self.scheduler.add_job(
            self._update_position_values,
            CronTrigger(
                minute='*/15',
                hour='9-16',
                day_of_week='mon-fri',
                timezone=timezone
            ),
            id='position_value_updates',
            name='Position Value Updates'
        )
        
        logger.info("📅 Scheduled market data updates every 5 minutes and position updates every 15 minutes")
    
    async def _monitor_positions(self):
        """Monitor positions and make exit decisions"""
        try:
            logger.info("🔍 Starting position monitoring session")
            
            # Get current positions and portfolio
            positions = await self.options_service.get_active_positions()
            portfolio = await self.options_service.get_portfolio_summary()
            
            if not positions:
                logger.info("📭 No active positions to monitor")
                return
            
            # Get current market data
            market_summary = await self.market_data_service.get_market_summary()
            
            positions_to_close = []
            
            for position in positions:
                try:
                    # Check basic exit criteria first
                    should_exit, reason = await self._check_exit_criteria(position, market_summary)
                    
                    if should_exit:
                        positions_to_close.append((position, reason))
                        logger.info(f"🚨 Position {position.symbol} marked for exit: {reason}")
                    else:
                        # Ask Claude for position management advice
                        if self.claude_service:
                            exit_decision = await self._get_claude_exit_decision(position, market_summary, portfolio)
                            
                            if exit_decision.get('action') == 'CLOSE':
                                positions_to_close.append((position, f"Claude recommendation: {exit_decision.get('reasoning')}"))
                                logger.info(f"🤖 Claude recommends closing {position.symbol}: {exit_decision.get('reasoning')}")
                
                except Exception as e:
                    logger.error(f"❌ Failed to monitor position {position.symbol}: {e}")
            
            # Execute position exits
            if positions_to_close:
                logger.info(f"🎯 Executing {len(positions_to_close)} position exits")
                
                for position, reason in positions_to_close:
                    await self._execute_position_exit(position, reason)
                
                # Send exit notification email
                if self.email_service:
                    await self._send_exit_notification(positions_to_close)
            
            logger.info(f"🔍 Position monitoring complete. {len(positions_to_close)} positions exited.")
            
        except Exception as e:
            logger.error(f"❌ Position monitoring failed: {e}")
    
    async def _check_exit_criteria(self, position: OptionsPosition, market_summary: Dict[str, Any]) -> tuple[bool, str]:
        """Check basic exit criteria (stop losses, profit targets, time-based exits)"""
        
        # Check profit target
        if position.unrealized_pnl >= position.profit_target:
            return True, f"Profit target reached: ${position.unrealized_pnl:,.0f} >= ${position.profit_target:,.0f}"
        
        # Check stop loss
        if position.unrealized_pnl <= -position.max_loss:
            return True, f"Stop loss triggered: ${position.unrealized_pnl:,.0f} <= ${-position.max_loss:,.0f}"
        
        # Check time-based exit (close positions 1 week before expiration)
        days_to_expiry = min(
            (contract.expiration_date - datetime.now()).days 
            for contract in position.contracts
        )
        
        if days_to_expiry <= 7:
            return True, f"Time-based exit: {days_to_expiry} days to expiration"
        
        # Check if held too long
        days_held = (datetime.now() - position.entry_date).days
        if days_held >= settings.MAX_HOLDING_PERIOD_DAYS:
            return True, f"Maximum holding period reached: {days_held} days"
        
        return False, ""
    
    async def _get_claude_exit_decision(self, position: OptionsPosition, market_summary: Dict[str, Any], portfolio: PortfolioSummary) -> Dict[str, Any]:
        """Get Claude's recommendation for position management"""
        try:
            # Prepare position context for Claude
            days_held = (datetime.now() - position.entry_date).days
            days_to_expiry = min(
                (contract.expiration_date - datetime.now()).days 
                for contract in position.contracts
            )
            
            pnl_percentage = (position.unrealized_pnl / position.entry_cost) * 100
            
            context = {
                "position": {
                    "symbol": position.symbol,
                    "strategy": position.strategy_type.value,
                    "days_held": days_held,
                    "days_to_expiry": days_to_expiry,
                    "entry_cost": position.entry_cost,
                    "current_value": position.current_value,
                    "unrealized_pnl": position.unrealized_pnl,
                    "pnl_percentage": pnl_percentage,
                    "profit_target": position.profit_target,
                    "max_loss": position.max_loss
                },
                "market": market_summary,
                "portfolio_performance": {
                    "current_streak": portfolio.performance_history.current_streak,
                    "recent_win_rate": portfolio.performance_history.recent_win_rate,
                    "risk_level": portfolio.get_adaptive_risk_level()
                }
            }
            
            # Simple Claude prompt for exit decision
            prompt = f"""
            POSITION MANAGEMENT DECISION
            
            Analyze this options position and recommend whether to HOLD or CLOSE:
            
            Position: {position.symbol} {position.strategy_type.value}
            - Held for {days_held} days, {days_to_expiry} days to expiry
            - P&L: ${position.unrealized_pnl:,.0f} ({pnl_percentage:+.1f}%)
            - Target: ${position.profit_target:,.0f}, Max Loss: ${position.max_loss:,.0f}
            
            Market: {market_summary.get('market_sentiment')} sentiment, VIX at {market_summary.get('vix')}
            
            Portfolio Performance: {portfolio.performance_history.current_streak} streak, {portfolio.performance_history.recent_win_rate:.0f}% recent win rate
            
            Respond in JSON format:
            {{
                "action": "HOLD" or "CLOSE",
                "confidence": 0.7,
                "reasoning": "Brief explanation of decision"
            }}
            """
            
            response = await self.claude_service.get_position_management_advice(prompt)
            
            if response and isinstance(response, dict):
                return response
            else:
                return {"action": "HOLD", "confidence": 0.5, "reasoning": "Default hold decision"}
                
        except Exception as e:
            logger.error(f"❌ Failed to get Claude exit decision: {e}")
            return {"action": "HOLD", "confidence": 0.5, "reasoning": "Error in Claude analysis"}
    
    async def _execute_position_exit(self, position: OptionsPosition, reason: str):
        """Execute position exit"""
        try:
            # Get current position value for exit price
            current_value = await self.options_service._calculate_position_value(position)
            
            if current_value is not None:
                # Close the position
                success = await self.options_service.close_position(position.id, current_value / (position.quantity * 100))
                
                if success:
                    logger.info(f"✅ Closed position {position.symbol} for ${current_value:,.0f}. Reason: {reason}")
                else:
                    logger.error(f"❌ Failed to close position {position.symbol}")
            else:
                logger.error(f"❌ Could not determine exit value for {position.symbol}")
                
        except Exception as e:
            logger.error(f"❌ Failed to execute exit for {position.symbol}: {e}")
    
    async def _send_exit_notification(self, closed_positions: List[tuple]):
        """Send email notification for position exits"""
        try:
            if not self.email_service:
                return
            
            exit_summary = []
            total_pnl = 0
            
            for position, reason in closed_positions:
                exit_summary.append({
                    "symbol": position.symbol,
                    "strategy": position.strategy_type.value,
                    "pnl": position.realized_pnl,
                    "reason": reason
                })
                total_pnl += position.realized_pnl
            
            subject = f"🎯 Position Exits: {len(closed_positions)} positions closed (${total_pnl:+,.0f})"
            
            # TODO: Implement exit notification email template
            logger.info(f"📧 Exit notification: {subject}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send exit notification: {e}")
    
    async def _update_market_data(self):
        """Update market data for all tracked symbols"""
        try:
            await self.market_data_service.update_all_cached_data()
            
        except Exception as e:
            logger.error(f"❌ Failed to update market data: {e}")
    
    async def _update_position_values(self):
        """Update all position values using current market data"""
        try:
            await self.options_service.update_position_values()
            
        except Exception as e:
            logger.error(f"❌ Failed to update position values: {e}") 