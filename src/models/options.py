"""
Options Trading Data Models
Pydantic models for options positions, Greeks, strategies, and Claude decisions
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Enums
class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"

class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    EXPIRED = "expired"
    ASSIGNED = "assigned"

class StrategyType(str, Enum):
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    CALL_SPREAD = "call_spread"
    PUT_SPREAD = "put_spread"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    IRON_CONDOR = "iron_condor"
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"

class ClaudeActionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    ADJUST = "adjust"
    ROLL = "roll"
    CLOSE = "close"

# Pydantic Models
class GreeksData(BaseModel):
    """Options Greeks data"""
    delta: float = Field(..., description="Price sensitivity to underlying")
    gamma: float = Field(..., description="Delta sensitivity to underlying price")
    theta: float = Field(..., description="Time decay per day")
    vega: float = Field(..., description="Volatility sensitivity")
    rho: float = Field(..., description="Interest rate sensitivity")
    
    @validator('delta')
    def validate_delta(cls, v):
        if not -1 <= v <= 1:
            raise ValueError('Delta must be between -1 and 1')
        return v

class VolatilityData(BaseModel):
    """Volatility analysis data"""
    implied_volatility: float = Field(..., description="Current implied volatility")
    historical_volatility: float = Field(..., description="Historical volatility (30-day)")
    iv_rank: float = Field(..., description="IV rank (0-100)")
    iv_percentile: float = Field(..., description="IV percentile (0-100)")
    
    @property
    def iv_premium(self) -> float:
        """Calculate IV premium over HV"""
        return self.implied_volatility - self.historical_volatility

class OptionContract(BaseModel):
    """Individual option contract"""
    symbol: str = Field(..., description="Underlying symbol")
    strike: float = Field(..., description="Strike price")
    expiration: date = Field(..., description="Expiration date")
    option_type: OptionType = Field(..., description="Call or Put")
    
    # Market data
    bid: float = Field(0.0, description="Current bid price")
    ask: float = Field(0.0, description="Current ask price")
    last: float = Field(0.0, description="Last traded price")
    volume: int = Field(0, description="Daily volume")
    open_interest: int = Field(0, description="Open interest")
    
    # Greeks and volatility
    greeks: Optional[GreeksData] = None
    volatility: Optional[VolatilityData] = None
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price from bid/ask"""
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        return self.last
    
    @property
    def days_to_expiration(self) -> int:
        """Calculate days until expiration"""
        return (self.expiration - date.today()).days
    
    @property
    def option_symbol(self) -> str:
        """Generate standard option symbol"""
        exp_str = self.expiration.strftime("%y%m%d")
        strike_str = f"{int(self.strike * 1000):08d}"
        type_str = "C" if self.option_type == OptionType.CALL else "P"
        return f"{self.symbol}{exp_str}{type_str}{strike_str}"

class ClaudeDecision(BaseModel):
    """Claude AI decision for a position"""
    id: UUID = Field(default_factory=uuid4)
    position_id: UUID = Field(..., description="Associated position ID")
    conversation_id: str = Field(..., description="Claude conversation thread ID")
    
    # Decision details
    action: ClaudeActionType = Field(..., description="Recommended action")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level (0-1)")
    reasoning: str = Field(..., description="Claude's reasoning for the decision")
    
    # Market analysis
    market_outlook: str = Field(..., description="Claude's market outlook")
    volatility_assessment: str = Field(..., description="Volatility analysis")
    risk_assessment: str = Field(..., description="Risk evaluation")
    
    # Specific recommendations
    target_price: Optional[float] = Field(None, description="Target exit price")
    stop_loss: Optional[float] = Field(None, description="Stop loss level")
    time_horizon: Optional[int] = Field(None, description="Recommended holding days")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    market_data_snapshot: Dict[str, Any] = Field(default_factory=dict)

class OptionsPosition(BaseModel):
    """Options trading position"""
    id: UUID = Field(default_factory=uuid4)
    strategy_type: StrategyType = Field(..., description="Options strategy type")
    status: PositionStatus = Field(default=PositionStatus.OPEN)
    
    # Basic position info
    symbol: str = Field(..., description="Underlying symbol")
    quantity: int = Field(..., description="Number of contracts")
    entry_date: datetime = Field(default_factory=datetime.utcnow)
    exit_date: Optional[datetime] = None
    
    # Financial details
    entry_cost: float = Field(..., description="Total cost to enter position")
    current_value: float = Field(0.0, description="Current position value")
    realized_pnl: float = Field(0.0, description="Realized P&L")
    unrealized_pnl: float = Field(0.0, description="Unrealized P&L")
    
    # Options contracts in this position
    contracts: List[OptionContract] = Field(default_factory=list)
    
    # Position Greeks (aggregated)
    portfolio_delta: float = Field(0.0, description="Total position delta")
    portfolio_gamma: float = Field(0.0, description="Total position gamma")
    portfolio_theta: float = Field(0.0, description="Total position theta")
    portfolio_vega: float = Field(0.0, description="Total position vega")
    
    # Claude integration
    claude_conversation_id: str = Field(..., description="Individual Claude conversation")
    claude_decisions: List[ClaudeDecision] = Field(default_factory=list)
    last_claude_check: Optional[datetime] = None
    
    # Risk management
    max_loss: float = Field(..., description="Maximum acceptable loss")
    profit_target: float = Field(..., description="Profit target")
    
    @property
    def total_pnl(self) -> float:
        """Total P&L (realized + unrealized)"""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def pnl_percentage(self) -> float:
        """P&L as percentage of entry cost"""
        if self.entry_cost == 0:
            return 0.0
        return (self.total_pnl / self.entry_cost) * 100
    
    @property
    def days_held(self) -> int:
        """Days position has been held"""
        end_date = self.exit_date or datetime.utcnow()
        return (end_date - self.entry_date).days
    
    def should_check_with_claude(self) -> bool:
        """Determine if position needs Claude check-in"""
        if not self.last_claude_check:
            return True
        
        # Check if significant move (>25%)
        if abs(self.pnl_percentage) > 25:
            return True
        
        # Check if approaching expiration (7 days)
        min_days_to_exp = min(c.days_to_expiration for c in self.contracts)
        if min_days_to_exp <= 7:
            return True
        
        # Check if it's been more than 24 hours
        hours_since_check = (datetime.utcnow() - self.last_claude_check).total_seconds() / 3600
        if hours_since_check > 24:
            return True
        
        return False

class PerformanceHistory(BaseModel):
    """Historical performance tracking for adaptive risk management"""
    
    # Recent performance trends
    last_7_days_pnl: float = Field(0.0, description="P&L over last 7 days")
    last_30_days_pnl: float = Field(0.0, description="P&L over last 30 days")
    last_60_days_pnl: float = Field(0.0, description="P&L over last 60 days")
    
    # Win/Loss streaks
    current_streak: int = Field(0, description="Current win/loss streak (positive=wins, negative=losses)")
    longest_winning_streak: int = Field(0, description="Longest winning streak")
    longest_losing_streak: int = Field(0, description="Longest losing streak") 
    
    # Strategy effectiveness
    recent_win_rate: float = Field(0.0, description="Win rate over last 20 trades")
    strategy_performance: Dict[str, float] = Field(default_factory=dict, description="Performance by strategy type")
    
    # Risk metrics
    consecutive_losses: int = Field(0, description="Number of consecutive losing trades")
    days_since_last_win: int = Field(0, description="Days since last profitable trade")
    volatility_of_returns: float = Field(0.0, description="Standard deviation of daily returns")
    
    # Confidence indicators
    performance_trend: str = Field("neutral", description="improving|declining|stable|neutral")
    risk_confidence: float = Field(0.5, description="Confidence in current strategy (0-1)")
    suggested_risk_adjustment: str = Field("maintain", description="increase|decrease|maintain")

class PortfolioSummary(BaseModel):
    """Portfolio-wide summary and risk metrics"""
    total_value: float = Field(..., description="Total portfolio value")
    cash_balance: float = Field(..., description="Available cash")
    total_pnl: float = Field(..., description="Total P&L across all positions")
    
    # Portfolio Greeks
    total_delta: float = Field(0.0, description="Portfolio delta exposure")
    total_gamma: float = Field(0.0, description="Portfolio gamma exposure")
    total_theta: float = Field(0.0, description="Portfolio theta (daily decay)")
    total_vega: float = Field(0.0, description="Portfolio vega (vol sensitivity)")
    
    # Risk metrics
    max_drawdown: float = Field(0.0, description="Maximum drawdown")
    win_rate: float = Field(0.0, description="Percentage of winning trades")
    average_win: float = Field(0.0, description="Average winning trade size")
    average_loss: float = Field(0.0, description="Average losing trade size")
    
    # Position summary
    open_positions: int = Field(0, description="Number of open positions")
    positions_by_strategy: Dict[StrategyType, int] = Field(default_factory=dict)
    
    # Enhanced performance tracking
    performance_history: PerformanceHistory = Field(default_factory=PerformanceHistory, description="Historical performance data")
    
    @property
    def portfolio_utilization(self) -> float:
        """Percentage of capital deployed"""
        total_capital = self.total_value + self.cash_balance
        if total_capital == 0:
            return 0.0
        return (self.total_value / total_capital) * 100
    
    @property
    def risk_adjusted_confidence(self) -> float:
        """Calculate confidence level based on recent performance"""
        base_confidence = 0.5
        
        # Adjust based on recent performance
        if self.performance_history.last_30_days_pnl > 0:
            base_confidence += 0.2
        elif self.performance_history.last_30_days_pnl < -1000:
            base_confidence -= 0.3
            
        # Adjust based on win streaks
        if self.performance_history.current_streak > 3:
            base_confidence += 0.15
        elif self.performance_history.current_streak < -2:
            base_confidence -= 0.25
            
        # Adjust based on consecutive losses
        if self.performance_history.consecutive_losses >= 3:
            base_confidence -= 0.4
            
        return max(0.1, min(0.9, base_confidence))
    
    @property 
    def suggested_position_size_multiplier(self) -> float:
        """Suggest position size adjustment based on performance"""
        multiplier = 1.0
        
        # Reduce size after losses
        if self.performance_history.consecutive_losses >= 3:
            multiplier *= 0.5
        elif self.performance_history.consecutive_losses >= 2:
            multiplier *= 0.7
            
        # Increase size after wins (but cap it)
        if self.performance_history.current_streak > 3:
            multiplier *= 1.2
        elif self.performance_history.current_streak > 5:
            multiplier *= 1.3
            
        # Cap the adjustments
        return max(0.3, min(1.5, multiplier))
    
    def get_adaptive_risk_level(self) -> str:
        """Get recommended risk level based on performance history"""
        if self.performance_history.consecutive_losses >= 3:
            return "very_conservative"
        elif self.performance_history.consecutive_losses >= 2:
            return "conservative"
        elif self.performance_history.current_streak > 3 and self.performance_history.last_30_days_pnl > 1000:
            return "moderate_aggressive"
        elif self.performance_history.current_streak > 5:
            return "aggressive"
        else:
            return "normal"

# SQLAlchemy Database Models
class PositionDB(Base):
    __tablename__ = "positions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="open")
    symbol = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    exit_date = Column(DateTime, nullable=True)
    entry_cost = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    claude_conversation_id = Column(String(100), nullable=False)
    last_claude_check = Column(DateTime, nullable=True)
    max_loss = Column(Float, nullable=False)
    profit_target = Column(Float, nullable=False)
    
    # Portfolio Greeks
    portfolio_delta = Column(Float, default=0.0)
    portfolio_gamma = Column(Float, default=0.0)
    portfolio_theta = Column(Float, default=0.0)
    portfolio_vega = Column(Float, default=0.0)
    
    # JSON fields for flexibility
    contracts_data = Column(JSONB, nullable=False)
    position_metadata = Column(JSONB, default={})
    
    # Relationships
    claude_decisions = relationship("ClaudeDecisionDB", back_populates="position")

class ClaudeDecisionDB(Base):
    __tablename__ = "claude_decisions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    position_id = Column(PGUUID(as_uuid=True), ForeignKey("positions.id"), nullable=False)
    conversation_id = Column(String(100), nullable=False)
    action = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    market_outlook = Column(Text, nullable=False)
    volatility_assessment = Column(Text, nullable=False)
    risk_assessment = Column(Text, nullable=False)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    time_horizon = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    market_data_snapshot = Column(JSONB, default={})
    
    # Relationships
    position = relationship("PositionDB", back_populates="claude_decisions")

class TradingSessionDB(Base):
    __tablename__ = "trading_sessions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_type = Column(String(20), nullable=False)  # morning, evening, intraday
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    claude_queries_used = Column(Integer, default=0)
    positions_analyzed = Column(Integer, default=0)
    trades_executed = Column(Integer, default=0)
    session_summary = Column(JSONB, default={})
    errors = Column(JSONB, default=[]) 