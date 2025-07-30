"""
Options Service - Paper Trading Implementation with Autonomous Execution
Handles options execution, Greeks calculation, position management, auto-trading, and database persistence
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.options import OptionsPosition, OptionContract, PortfolioSummary, StrategyType, PositionDB, PerformanceHistory
from src.core.config import settings
from src.core.database import get_db
from src.services.market_data_service import MarketDataService
from sqlalchemy import select

logger = logging.getLogger(__name__)

class OptionsService:
    """Options trading service with paper trading support, autonomous execution, and database persistence"""
    
    def __init__(self):
        self.paper_trading_enabled = settings.PAPER_TRADING_ONLY
        self.positions: Dict[UUID, OptionsPosition] = {}
        self.portfolio_value = 100000.0  # Starting paper trading capital
        self.cash_balance = 100000.0
        self.daily_trades_count = 0
        self.last_trade_date = None
        self._positions_loaded = False
        self.market_data_service = MarketDataService()
    
    async def initialize(self):
        """Initialize service and load positions from database"""
        if not self._positions_loaded:
            await self._load_positions_from_db()
            self._positions_loaded = True
            logger.info(f"📊 OptionsService initialized with {len(self.positions)} positions")
    
    async def _load_positions_from_db(self):
        """Load existing positions from database on startup"""
        try:
            async for db in get_db():
                # Use async SQLAlchemy syntax
                result = await db.execute(select(PositionDB).where(PositionDB.status == "open"))
                db_positions = result.scalars().all()
                
                for db_pos in db_positions:
                    # Convert database position to in-memory position
                    position = self._db_position_to_model(db_pos)
                    if position:
                        self.positions[position.id] = position
                        logger.info(f"📥 Loaded position: {position.symbol} {position.strategy_type.value}")
                
                # Recalculate portfolio values based on loaded positions
                await self._recalculate_portfolio_from_positions()
                
                logger.info(f"📥 Loaded {len(self.positions)} active positions from database")
                break  # Only need one database session
            
        except Exception as e:
            logger.error(f"❌ Failed to load positions from database: {e}")
    
    def _db_position_to_model(self, db_pos: PositionDB) -> Optional[OptionsPosition]:
        """Convert database PositionDB to OptionsPosition model"""
        try:
            # Reconstruct option contracts from JSON data
            contracts = []
            for contract_data in db_pos.contracts_data:
                contract = OptionContract(**contract_data)
                contracts.append(contract)
            
            # Create OptionsPosition object
            position = OptionsPosition(
                id=db_pos.id,
                strategy_type=StrategyType(db_pos.strategy_type),
                status=db_pos.status,
                symbol=db_pos.symbol,
                quantity=db_pos.quantity,
                entry_date=db_pos.entry_date,
                exit_date=db_pos.exit_date,
                entry_cost=db_pos.entry_cost,
                current_value=db_pos.current_value,
                realized_pnl=db_pos.realized_pnl,
                unrealized_pnl=db_pos.unrealized_pnl,
                contracts=contracts,
                claude_conversation_id=db_pos.claude_conversation_id,
                last_claude_check=db_pos.last_claude_check,
                max_loss=db_pos.max_loss,
                profit_target=db_pos.profit_target,
                portfolio_delta=db_pos.portfolio_delta,
                portfolio_gamma=db_pos.portfolio_gamma,
                portfolio_theta=db_pos.portfolio_theta,
                portfolio_vega=db_pos.portfolio_vega,
                position_metadata=db_pos.position_metadata or {}
            )
            
            return position
            
        except Exception as e:
            logger.error(f"❌ Failed to convert database position to model: {e}")
            return None
    
    async def _save_position_to_db(self, position: OptionsPosition):
        """Save position to database"""
        try:
            db = next(get_db())
            
            # Check if position already exists
            existing = db.query(PositionDB).filter(PositionDB.id == position.id).first()
            
            if existing:
                # Update existing position
                existing.status = position.status
                existing.current_value = position.current_value
                existing.realized_pnl = position.realized_pnl
                existing.unrealized_pnl = position.unrealized_pnl
                existing.exit_date = position.exit_date
                existing.last_claude_check = position.last_claude_check
                existing.portfolio_delta = position.portfolio_delta
                existing.portfolio_gamma = position.portfolio_gamma
                existing.portfolio_theta = position.portfolio_theta
                existing.portfolio_vega = position.portfolio_vega
                existing.position_metadata = position.position_metadata
                logger.info(f"💾 Updated position in database: {position.symbol}")
            else:
                # Create new position
                contracts_data = [contract.dict() for contract in position.contracts]
                
                db_position = PositionDB(
                    id=position.id,
                    strategy_type=position.strategy_type.value,
                    status=position.status,
                    symbol=position.symbol,
                    quantity=position.quantity,
                    entry_date=position.entry_date,
                    exit_date=position.exit_date,
                    entry_cost=position.entry_cost,
                    current_value=position.current_value,
                    realized_pnl=position.realized_pnl,
                    unrealized_pnl=position.unrealized_pnl,
                    claude_conversation_id=position.claude_conversation_id,
                    last_claude_check=position.last_claude_check,
                    max_loss=position.max_loss,
                    profit_target=position.profit_target,
                    portfolio_delta=position.portfolio_delta,
                    portfolio_gamma=position.portfolio_gamma,
                    portfolio_theta=position.portfolio_theta,
                    portfolio_vega=position.portfolio_vega,
                    contracts_data=contracts_data,
                    position_metadata=position.position_metadata
                )
                
                db.add(db_position)
                logger.info(f"💾 Saved new position to database: {position.symbol}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"❌ Failed to save position to database: {e}")
            db.rollback()
    
    async def _recalculate_portfolio_from_positions(self):
        """Recalculate portfolio value and cash balance from actual positions"""
        total_position_value = sum(pos.current_value for pos in self.positions.values() if pos.status == "open")
        total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values() if pos.status == "closed")
        
        # Calculate current portfolio value
        self.portfolio_value = 100000.0 + total_realized_pnl + sum(pos.unrealized_pnl for pos in self.positions.values() if pos.status == "open")
        
        # Calculate available cash (starting cash - position costs + realized gains/losses)
        total_position_costs = sum(pos.entry_cost for pos in self.positions.values() if pos.status == "open")
        self.cash_balance = 100000.0 - total_position_costs + total_realized_pnl
        
        logger.info(f"📊 Portfolio recalculated: Value=${self.portfolio_value:,.0f}, Cash=${self.cash_balance:,.0f}, Positions={len([p for p in self.positions.values() if p.status == 'open'])}")
    
    async def get_portfolio_summary(self) -> PortfolioSummary:
        """Get current portfolio summary with real position data"""
        await self.initialize()  # Ensure positions are loaded
        
        # Calculate real metrics from actual positions
        open_positions = [pos for pos in self.positions.values() if pos.status == "open"]
        closed_positions = [pos for pos in self.positions.values() if pos.status == "closed"]
        
        total_pnl = sum(pos.realized_pnl for pos in closed_positions) + sum(pos.unrealized_pnl for pos in open_positions)
        
        # Calculate win rate from actual trading history
        win_rate = 0.0
        average_win = 0.0
        average_loss = 0.0
        max_drawdown = 0.0
        
        if closed_positions:
            winning_trades = [pos for pos in closed_positions if pos.realized_pnl > 0]
            losing_trades = [pos for pos in closed_positions if pos.realized_pnl < 0]
            
            win_rate = (len(winning_trades) / len(closed_positions)) * 100
            average_win = sum(pos.realized_pnl for pos in winning_trades) / len(winning_trades) if winning_trades else 0
            average_loss = sum(pos.realized_pnl for pos in losing_trades) / len(losing_trades) if losing_trades else 0
            
            # Calculate max drawdown (simplified)
            running_total = 0
            peak = 0
            max_dd = 0
            for pos in sorted(closed_positions, key=lambda x: x.exit_date or datetime.now()):
                running_total += pos.realized_pnl
                peak = max(peak, running_total)
                drawdown = peak - running_total
                max_dd = max(max_dd, drawdown)
            
            max_drawdown = (max_dd / 100000.0) * 100 if max_dd > 0 else 0  # As percentage
        
        # Calculate performance history (simplified - in production this would be more sophisticated)
        performance_history = self._calculate_performance_history(closed_positions)
        
        return PortfolioSummary(
            total_value=self.portfolio_value,
            cash_balance=self.cash_balance,
            total_pnl=total_pnl,
            open_positions=len(open_positions),
            win_rate=win_rate,
            average_win=average_win,
            average_loss=average_loss,
            max_drawdown=max_drawdown,
            total_delta=sum(pos.portfolio_delta for pos in open_positions),
            total_gamma=sum(pos.portfolio_gamma for pos in open_positions),
            total_theta=sum(pos.portfolio_theta for pos in open_positions),
            total_vega=sum(pos.portfolio_vega for pos in open_positions),
            performance_history=performance_history
        )
    
    def _calculate_performance_history(self, closed_positions: List[OptionsPosition]) -> PerformanceHistory:
        """Calculate performance history from actual trading data"""
        if not closed_positions:
            return PerformanceHistory()
        
        # Sort positions by exit date
        sorted_positions = sorted(closed_positions, key=lambda x: x.exit_date or datetime.now())
        
        # Calculate recent P&L
        now = datetime.now()
        last_7_days = [pos for pos in sorted_positions if pos.exit_date and (now - pos.exit_date).days <= 7]
        last_30_days = [pos for pos in sorted_positions if pos.exit_date and (now - pos.exit_date).days <= 30]
        last_60_days = [pos for pos in sorted_positions if pos.exit_date and (now - pos.exit_date).days <= 60]
        
        last_7_days_pnl = sum(pos.realized_pnl for pos in last_7_days)
        last_30_days_pnl = sum(pos.realized_pnl for pos in last_30_days)
        last_60_days_pnl = sum(pos.realized_pnl for pos in last_60_days)
        
        # Calculate streaks
        current_streak = 0
        consecutive_losses = 0
        
        if sorted_positions:
            # Count current streak from most recent trades
            for pos in reversed(sorted_positions):
                if current_streak == 0:
                    current_streak = 1 if pos.realized_pnl > 0 else -1
                elif (current_streak > 0 and pos.realized_pnl > 0) or (current_streak < 0 and pos.realized_pnl < 0):
                    current_streak += 1 if current_streak > 0 else -1
                else:
                    break
            
            # Count consecutive losses from the end
            for pos in reversed(sorted_positions):
                if pos.realized_pnl < 0:
                    consecutive_losses += 1
                else:
                    break
        
        # Calculate recent win rate (last 20 trades)
        recent_trades = sorted_positions[-20:] if len(sorted_positions) >= 20 else sorted_positions
        recent_wins = len([pos for pos in recent_trades if pos.realized_pnl > 0])
        recent_win_rate = (recent_wins / len(recent_trades)) * 100 if recent_trades else 0
        
        # Determine performance trend
        if last_30_days_pnl > last_60_days_pnl * 0.5:  # Improving if last 30 days > half of last 60 days
            trend = "improving"
        elif last_30_days_pnl < 0 and last_7_days_pnl < 0:
            trend = "declining"
        else:
            trend = "stable"
        
        # Calculate days since last win
        days_since_last_win = 0
        if sorted_positions:
            for pos in reversed(sorted_positions):
                if pos.realized_pnl > 0:
                    days_since_last_win = (now - pos.exit_date).days if pos.exit_date else 0
                    break
                days_since_last_win += 1
        
        return PerformanceHistory(
            last_7_days_pnl=last_7_days_pnl,
            last_30_days_pnl=last_30_days_pnl,
            last_60_days_pnl=last_60_days_pnl,
            current_streak=current_streak,
            consecutive_losses=consecutive_losses,
            days_since_last_win=days_since_last_win,
            recent_win_rate=recent_win_rate,
            performance_trend=trend,
            risk_confidence=max(0.1, min(0.9, 0.5 + (recent_win_rate - 50) / 100)),
            strategy_performance={}  # TODO: Calculate by strategy type
        )
    
    async def enable_paper_trading(self):
        """Enable paper trading mode"""
        self.paper_trading_enabled = True
        logger.info("📝 Paper trading mode enabled")
    
    async def get_active_positions(self) -> List[OptionsPosition]:
        """Get all active positions"""
        await self.initialize()  # Ensure positions are loaded
        return [pos for pos in self.positions.values() if pos.status == "open"]
    
    def reset_daily_counter(self):
        """Reset daily trade counter at start of new day"""
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.daily_trades_count = 0
            self.last_trade_date = today
            logger.info(f"🔄 Reset daily trade counter for {today}")
    
    async def create_position(self, position: OptionsPosition) -> bool:
        """Create a new options position with database persistence"""
        if not self.paper_trading_enabled:
            logger.error("Live trading not implemented yet")
            return False
        
        try:
            # Add to in-memory storage
            self.positions[position.id] = position
            self.cash_balance -= position.entry_cost
            
            # Save to database
            await self._save_position_to_db(position)
            
            logger.info(f"📝 Paper trade: Created {position.symbol} position for ${position.entry_cost:,.0f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create position: {e}")
            # Rollback in-memory changes if database save failed
            if position.id in self.positions:
                del self.positions[position.id]
                self.cash_balance += position.entry_cost
            return False
    
    async def close_position(self, position_id: UUID, exit_price: float) -> bool:
        """Close an options position with database persistence"""
        if position_id not in self.positions:
            return False
        
        try:
            position = self.positions[position_id]
            position.status = "closed"
            position.exit_date = datetime.now()
            position.current_value = exit_price * position.quantity
            position.realized_pnl = position.current_value - position.entry_cost
            position.unrealized_pnl = 0.0  # No longer unrealized
            
            self.cash_balance += position.current_value
            
            # Save to database
            await self._save_position_to_db(position)
            
            logger.info(f"📝 Paper trade: Closed {position.symbol} position. P&L: ${position.realized_pnl:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to close position: {e}")
            return False
    
    async def update_position_values(self):
        """Update current values for all open positions using real market data"""
        try:
            updated_count = 0
            
            for position in self.positions.values():
                if position.status == "open":
                    # Get real market data for the underlying symbol
                    new_value = await self._calculate_position_value(position)
                    
                    if new_value is not None:
                        old_value = position.current_value
                        position.current_value = new_value
                        position.unrealized_pnl = new_value - position.entry_cost
                        
                        # Save to database if significant change
                        if abs(new_value - old_value) > 10:  # Only save if change > $10
                            await self._save_position_to_db(position)
                            updated_count += 1
                            
                            logger.debug(f"📊 Updated {position.symbol}: ${new_value:,.0f} (P&L: ${position.unrealized_pnl:+,.0f})")
            
            if updated_count > 0:
                logger.info(f"📊 Updated {updated_count} position values using market data")
                
        except Exception as e:
            logger.error(f"❌ Failed to update position values: {e}")
    
    async def _calculate_position_value(self, position: OptionsPosition) -> Optional[float]:
        """Calculate current position value using market data and option pricing"""
        try:
            total_value = 0.0
            
            for contract in position.contracts:
                # Get current option price using market data
                option_price = await self.market_data_service.get_option_price(
                    symbol=position.symbol,
                    strike=contract.strike_price,
                    expiration=contract.expiration_date,
                    option_type=contract.option_type
                )
                
                if option_price is not None:
                    # Calculate value: price * quantity * 100 (option multiplier)
                    contract_value = option_price * abs(contract.quantity) * 100
                    
                    # If we're short the option, value is negative impact on position
                    if contract.quantity < 0:
                        contract_value = -contract_value
                    
                    total_value += contract_value
                else:
                    # Fallback to previous calculation if market data fails
                    logger.warning(f"⚠️ No market data for {position.symbol} option, using fallback pricing")
                    return position.current_value * random.uniform(0.9, 1.1)  # ±10% random movement
            
            return max(0.01, total_value)  # Minimum $0.01 position value
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate position value for {position.symbol}: {e}")
            return None
    
    def get_position(self, position_id: UUID) -> Optional[OptionsPosition]:
        """Get a specific position"""
        return self.positions.get(position_id) 
    
    async def create_position_from_opportunity(self, opportunity: Dict[str, Any], portfolio: PortfolioSummary) -> Optional[OptionsPosition]:
        """
        Convert Claude opportunity into executable OptionsPosition using REAL option chain data
        
        Takes Claude's recommendation and creates a real position object
        with live option pricing, real Greeks, and market-based position sizing
        """
        try:
            # Validate opportunity structure
            required_fields = ['symbol', 'strategy_type', 'confidence', 'target_return', 'max_risk']
            for field in required_fields:
                if field not in opportunity:
                    logger.error(f"❌ Missing required field '{field}' in opportunity")
                    return None
            
            # Extract opportunity details
            symbol = opportunity['symbol']
            strategy_type = StrategyType(opportunity['strategy_type'])
            confidence = opportunity['confidence']
            target_return = opportunity['target_return']
            max_risk = opportunity['max_risk']
            time_horizon_days = opportunity.get('time_horizon_days', 21)
            strike_price = opportunity.get('strike_price')
            
            # Calculate position sizing based on portfolio and risk
            position_size = self._calculate_position_size(max_risk, portfolio)
            
            # Get REAL option chain data for the symbol
            logger.info(f"📊 Fetching live option chain for {symbol}...")
            option_chain = await self.market_data_service.get_option_chain(symbol)
            
            if not option_chain:
                logger.error(f"❌ Could not get live option chain for {symbol}")
                return None
            
            # Generate REAL option contracts based on live market data
            contracts = await self._create_real_option_contracts(
                symbol, strategy_type, position_size, option_chain, strike_price, time_horizon_days
            )
            
            if not contracts:
                logger.error(f"❌ Could not create real option contracts for {symbol} {strategy_type.value}")
                return None
            
            # Calculate real Greeks from live option data
            portfolio_greeks = await self._calculate_real_greeks(contracts, option_chain)
            
            # Create position object with REAL data
            position = OptionsPosition(
                id=uuid4(),
                strategy_type=strategy_type,
                symbol=symbol,
                quantity=len(contracts),
                entry_date=datetime.now(),
                entry_cost=position_size,
                current_value=position_size,  # Starts at entry cost
                contracts=contracts,
                claude_conversation_id=f"live_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                max_loss=max_risk,
                profit_target=target_return,
                
                # Real Greeks from live option data
                portfolio_delta=portfolio_greeks['delta'],
                portfolio_gamma=portfolio_greeks['gamma'],
                portfolio_theta=portfolio_greeks['theta'],
                portfolio_vega=portfolio_greeks['vega'],
                
                # Additional metadata
                position_metadata={
                    "claude_confidence": confidence,
                    "expected_return": target_return,
                    "time_horizon_days": time_horizon_days,
                    "auto_created": True,
                    "data_source": "live_market",
                    "underlying_price": option_chain['underlying_price'],
                    "creation_timestamp": datetime.now().isoformat(),
                    "market_conditions": {
                        "implied_volatility": await self._get_average_iv(option_chain),
                        "time_to_expiry": time_horizon_days
                    }
                }
            )
            
            logger.info(f"📋 Created REAL position: {symbol} {strategy_type.value} (${position_size:,.0f}, {confidence:.1%} confidence)")
            logger.info(f"📊 Real Greeks: Δ={portfolio_greeks['delta']:.3f}, Γ={portfolio_greeks['gamma']:.3f}, Θ={portfolio_greeks['theta']:.2f}, ν={portfolio_greeks['vega']:.2f}")
            
            return position
            
        except Exception as e:
            logger.error(f"❌ Failed to create position from live opportunity: {e}")
            return None
    
    def _calculate_position_size(self, max_risk: float, portfolio: PortfolioSummary) -> float:
        """Calculate appropriate position size based on portfolio and risk"""
        # Use portfolio's suggested position size multiplier
        base_size = portfolio.cash_balance * (settings.DEFAULT_POSITION_SIZE_PCT / 100)
        adjusted_size = base_size * portfolio.suggested_position_size_multiplier
        
        # Don't exceed the max risk suggested by Claude
        position_size = min(adjusted_size, max_risk)
        
        # Ensure minimum and maximum bounds
        min_size = 500.0  # Minimum $500 position
        max_size = portfolio.cash_balance * 0.20  # Maximum 20% of cash
        
        return max(min_size, min(position_size, max_size))
    
    async def _create_real_option_contracts(self, symbol: str, strategy_type: StrategyType, position_size: float, option_chain: Dict[str, Any], target_strike: Optional[float], days_to_expiry: int) -> List[OptionContract]:
        """Create real option contracts using live option chain data"""
        try:
            contracts = []
            underlying_price = option_chain['underlying_price']
            expiration_date = datetime.now() + timedelta(days=days_to_expiry)
            
            # Calculate contract count based on position size (assuming ~$1000 per contract)
            base_contract_count = max(1, int(position_size / 1000))
            
            if strategy_type in [StrategyType.LONG_CALL]:
                # Find appropriate call strike from real option chain
                call_options = option_chain.get('calls', [])
                
                if target_strike:
                    # Use specific strike if provided by Claude
                    strike = self._find_closest_strike(call_options, target_strike)
                else:
                    # Select strike based on strategy and current price
                    if strategy_type == StrategyType.LONG_CALL:
                        # ATM or slightly OTM for long calls
                        strike = self._find_closest_strike(call_options, underlying_price * 1.02)
                    else:
                        # OTM for short calls
                        strike = self._find_closest_strike(call_options, underlying_price * 1.05)
                
                contracts.append(OptionContract(
                    option_type="call",
                    strike_price=strike,
                    expiration_date=expiration_date,
                    quantity=base_contract_count if strategy_type == StrategyType.LONG_CALL else -base_contract_count
                ))
                
            elif strategy_type in [StrategyType.LONG_PUT]:
                # Find appropriate put strike from real option chain
                put_options = option_chain.get('puts', [])
                
                if target_strike:
                    # Use specific strike if provided by Claude
                    strike = self._find_closest_strike(put_options, target_strike)
                else:
                    # Select strike based on strategy and current price
                    if strategy_type == StrategyType.LONG_PUT:
                        # ATM or slightly OTM for long puts
                        strike = self._find_closest_strike(put_options, underlying_price * 0.98)
                    else:
                        # OTM for short puts
                        strike = self._find_closest_strike(put_options, underlying_price * 0.95)
                
                contracts.append(OptionContract(
                    option_type="put",
                    strike_price=strike,
                    expiration_date=expiration_date,
                    quantity=base_contract_count if strategy_type == StrategyType.LONG_PUT else -base_contract_count
                ))
                
            elif strategy_type == StrategyType.CALL_SPREAD:
                # Create call spread using real option chain
                call_options = option_chain.get('calls', [])
                short_strike = self._find_closest_strike(call_options, underlying_price * 1.03)
                long_strike = self._find_closest_strike(call_options, underlying_price * 1.08)
                
                contracts.extend([
                    OptionContract(
                        option_type="call",
                        strike_price=short_strike,
                        expiration_date=expiration_date,
                        quantity=-base_contract_count  # Short
                    ),
                    OptionContract(
                        option_type="call",
                        strike_price=long_strike,
                        expiration_date=expiration_date,
                        quantity=base_contract_count   # Long
                    )
                ])
            elif strategy_type == StrategyType.PUT_SPREAD:
                # Create put spread using real option chain
                put_options = option_chain.get('puts', [])
                short_strike = self._find_closest_strike(put_options, underlying_price * 0.97)
                long_strike = self._find_closest_strike(put_options, underlying_price * 0.92)
                
                contracts.extend([
                    OptionContract(
                        option_type="put",
                        strike_price=short_strike,
                        expiration_date=expiration_date,
                        quantity=-base_contract_count  # Short
                    ),
                    OptionContract(
                        option_type="put",
                        strike_price=long_strike,
                        expiration_date=expiration_date,
                        quantity=base_contract_count   # Long
                    )
                ])
                    
            elif strategy_type == StrategyType.IRON_CONDOR:
                # Create iron condor using real option chain
                call_options = option_chain.get('calls', [])
                put_options = option_chain.get('puts', [])
                
                # Short strikes closer to underlying
                short_call_strike = self._find_closest_strike(call_options, underlying_price * 1.05)
                short_put_strike = self._find_closest_strike(put_options, underlying_price * 0.95)
                
                # Long strikes further from underlying
                long_call_strike = self._find_closest_strike(call_options, underlying_price * 1.10)
                long_put_strike = self._find_closest_strike(put_options, underlying_price * 0.90)
                
                contracts.extend([
                    # Short call spread
                    OptionContract(
                        option_type="call",
                        strike_price=short_call_strike,
                        expiration_date=expiration_date,
                        quantity=-base_contract_count
                    ),
                    OptionContract(
                        option_type="call",
                        strike_price=long_call_strike,
                        expiration_date=expiration_date,
                        quantity=base_contract_count
                    ),
                    # Short put spread
                    OptionContract(
                        option_type="put",
                        strike_price=short_put_strike,
                        expiration_date=expiration_date,
                        quantity=-base_contract_count
                    ),
                    OptionContract(
                        option_type="put",
                        strike_price=long_put_strike,
                        expiration_date=expiration_date,
                        quantity=base_contract_count
                    )
                ])
            
            logger.info(f"📊 Created {len(contracts)} real option contracts for {symbol} {strategy_type.value}")
            return contracts
            
        except Exception as e:
            logger.error(f"❌ Failed to create real option contracts: {e}")
            return []
    
    def _find_closest_strike(self, options_list: List[Dict], target_price: float) -> float:
        """Find the closest available strike price from real option chain"""
        if not options_list:
            return target_price
        
        closest_strike = target_price
        min_diff = float('inf')
        
        for option in options_list:
            strike = option.get('strike', 0)
            diff = abs(strike - target_price)
            if diff < min_diff:
                min_diff = diff
                closest_strike = strike
        
        return closest_strike
    
    async def _calculate_real_greeks(self, contracts: List[OptionContract], option_chain: Dict[str, Any]) -> Dict[str, float]:
        """Calculate real Greeks from live option chain data"""
        try:
            total_delta = 0.0
            total_gamma = 0.0
            total_theta = 0.0
            total_vega = 0.0
            
            for contract in contracts:
                # Find matching option in chain for real Greeks
                options_list = option_chain['calls'] if contract.option_type == 'call' else option_chain['puts']
                
                matching_option = None
                for option in options_list:
                    if abs(option.get('strike', 0) - contract.strike_price) < 0.01:
                        matching_option = option
                        break
                
                if matching_option:
                    # Use real Greeks from option chain
                    delta = matching_option.get('delta', 0.5)
                    gamma = matching_option.get('gamma', 0.01)
                    theta = matching_option.get('theta', -0.05)
                    vega = matching_option.get('vega', 0.1)
                    
                    # Apply contract quantity (negative for short positions)
                    multiplier = contract.quantity
                    
                    total_delta += delta * multiplier
                    total_gamma += gamma * multiplier
                    total_theta += theta * multiplier
                    total_vega += vega * multiplier
                else:
                    # Fallback to estimated Greeks if not available
                    logger.warning(f"⚠️ No Greeks data for {contract.option_type} {contract.strike_price}, using estimates")
                    if contract.option_type == 'call':
                        total_delta += 0.5 * contract.quantity
                    else:
                        total_delta += -0.5 * contract.quantity
                    
                    total_gamma += 0.01 * abs(contract.quantity)
                    total_theta += -0.05 * abs(contract.quantity)
                    total_vega += 0.1 * abs(contract.quantity)
            
            return {
                'delta': total_delta,
                'gamma': total_gamma,
                'theta': total_theta,
                'vega': total_vega
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate real Greeks: {e}")
            return {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0}
    
    async def _get_average_iv(self, option_chain: Dict[str, Any]) -> float:
        """Calculate average implied volatility from real option chain"""
        try:
            all_ivs = []
            
            # Collect IVs from calls
            for call in option_chain.get('calls', []):
                iv = call.get('impliedVolatility')
                if iv and iv > 0:
                    all_ivs.append(iv)
            
            # Collect IVs from puts
            for put in option_chain.get('puts', []):
                iv = put.get('impliedVolatility')
                if iv and iv > 0:
                    all_ivs.append(iv)
            
            if all_ivs:
                return sum(all_ivs) / len(all_ivs)
            else:
                return 0.25  # Default IV if no data
                
        except Exception as e:
            logger.error(f"❌ Failed to calculate average IV: {e}")
            return 0.25
    
    async def execute_approved_opportunities(self, opportunities: List[Dict[str, Any]], portfolio: PortfolioSummary) -> List[UUID]:
        """
        Execute approved opportunities automatically
        
        Returns list of position IDs that were successfully created
        """
        if not settings.AUTO_EXECUTE_TRADES:
            logger.info("🔒 Auto-execution disabled, skipping trade execution")
            return []
        
        self.reset_daily_counter()
        
        executed_positions = []
        
        for opportunity in opportunities:
            # Check daily limits
            if self.daily_trades_count >= settings.MAX_DAILY_POSITIONS:
                logger.warning(f"⚠️ Daily trade limit reached ({settings.MAX_DAILY_POSITIONS}), skipping remaining opportunities")
                break
            
            # Create position from opportunity
            position = await self.create_position_from_opportunity(opportunity, portfolio)
            if not position:
                continue
            
            # Execute the position
            success = await self.create_position(position)
            if success:
                executed_positions.append(position.id)
                self.daily_trades_count += 1
                logger.info(f"🎯 Executed position {self.daily_trades_count}/{settings.MAX_DAILY_POSITIONS}: {position.symbol} {position.strategy_type.value}")
            else:
                logger.error(f"❌ Failed to execute position: {position.symbol} {position.strategy_type.value}")
        
        if executed_positions:
            logger.info(f"✅ Successfully executed {len(executed_positions)} positions today")
        else:
            logger.info("📭 No positions executed today")
        
        return executed_positions 