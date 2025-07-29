# Claude AI Action Framework
## Comprehensive Trading Actions and Recommendations

### 1. Position Entry Actions

#### Stock Selection & Sizing
- **BUY**: Initiate new position with specific entry criteria
- **ACCUMULATE**: Add to existing position (dollar-cost averaging)
- **SCALE_IN**: Enter position in multiple tranches over time
- **WAIT**: Hold cash until better opportunity arises
- **POSITION_SIZE**: Recommend specific position size (% of portfolio)

#### Entry Timing & Parameters
- **ENTRY_PRICE_RANGE**: Set acceptable entry price band ($45.50 - $46.20)
- **TIME_LIMIT**: Maximum time to wait for entry (e.g., "expire if not filled by 2 PM")
- **VOLUME_CONDITION**: Only enter if volume > X shares traded
- **TECHNICAL_TRIGGER**: Wait for specific technical confirmation (RSI < 30, MACD cross, etc.)

### 2. Position Management Actions

#### Dynamic Adjustments
- **ADJUST_STOP_LOSS**: Modify stop-loss price based on price movement
- **TRAILING_STOP**: Implement trailing stop with specific distance
- **RAISE_TARGET**: Increase profit target based on momentum
- **LOWER_TARGET**: Reduce profit target if momentum weakens
- **EXTEND_HOLD**: Increase maximum holding period
- **SHORTEN_HOLD**: Reduce time horizon if conditions change

#### Position Sizing Changes
- **INCREASE_POSITION**: Add more shares to winning position
- **REDUCE_POSITION**: Trim position to lock in profits
- **REBALANCE**: Adjust position size relative to other holdings
- **HEDGE**: Add protective options or offsetting positions

### 3. Position Exit Actions

#### Standard Exits
- **SELL_ALL**: Exit entire position immediately
- **SELL_PARTIAL**: Sell specific percentage of position
- **SCALE_OUT**: Exit position in multiple tranches
- **PROFIT_TAKE**: Sell at specific profit target
- **STOP_LOSS**: Exit at predetermined loss limit

#### Advanced Exit Strategies
- **TIME_DECAY_EXIT**: Sell if no movement after X days
- **MOMENTUM_EXIT**: Exit if momentum indicators turn negative
- **VOLATILITY_EXIT**: Exit if volatility exceeds comfort level
- **NEWS_EXIT**: Immediate exit due to negative news/events
- **CORRELATION_EXIT**: Exit due to portfolio correlation risks

### 4. Risk Management Actions

#### Portfolio-Level Risk
- **REDUCE_EXPOSURE**: Lower overall market exposure
- **INCREASE_CASH**: Move to higher cash position
- **SECTOR_REBALANCE**: Adjust sector allocation
- **CORRELATION_CHECK**: Avoid positions that increase correlation
- **VOLATILITY_ADJUST**: Modify position sizes based on market volatility

#### Individual Position Risk
- **TIGHTEN_STOPS**: Reduce all stop-losses during high volatility
- **WIDEN_STOPS**: Allow more room during normal volatility
- **ADD_HEDGE**: Suggest protective puts or calls
- **PAIR_TRADE**: Recommend long/short pairs to reduce market exposure

### 5. Options Strategy Actions

#### Income Generation
- **COVERED_CALL**: Sell calls against stock positions
- **CASH_SECURED_PUT**: Sell puts to generate income
- **CALL_SPREAD**: Bull/bear call spreads for directional plays
- **PUT_SPREAD**: Bull/bear put spreads for income

#### Protection Strategies
- **PROTECTIVE_PUT**: Buy puts to limit downside
- **COLLAR**: Combine covered calls with protective puts
- **STRADDLE**: Buy volatility before earnings/events
- **IRON_CONDOR**: Profit from low volatility periods

### 6. Market Condition Actions

#### Bull Market Actions
- **INCREASE_BETA**: Target higher beta stocks for momentum
- **GROWTH_FOCUS**: Shift to growth-oriented positions
- **MOMENTUM_FOLLOW**: Follow trend momentum
- **LEVERAGE_UP**: Increase position sizes (within limits)

#### Bear Market Actions
- **DEFENSIVE_ROTATION**: Move to defensive sectors
- **CASH_PRESERVATION**: Increase cash allocation
- **SHORT_HEDGE**: Add short positions or inverse ETFs
- **QUALITY_FOCUS**: Focus on high-quality, profitable companies

#### Sideways Market Actions
- **RANGE_TRADING**: Buy support, sell resistance
- **THETA_STRATEGIES**: Focus on time-decay options strategies
- **DIVIDEND_FOCUS**: Target dividend-paying stocks
- **VOLATILITY_SELLING**: Sell premium through options

### 7. Event-Driven Actions

#### Earnings Responses
- **PRE_EARNINGS_EXIT**: Exit before earnings announcement
- **POST_EARNINGS_ENTRY**: Enter after earnings reaction
- **EARNINGS_STRADDLE**: Play volatility around earnings
- **GUIDANCE_REACTION**: Adjust based on forward guidance

#### Economic Events
- **FED_POSITIONING**: Adjust before Fed announcements
- **SECTOR_ROTATION**: Rotate based on economic data
- **CURRENCY_HEDGE**: Hedge currency exposure
- **INTEREST_RATE_PLAY**: Position for rate changes

### 8. Technical Analysis Actions

#### Trend Following
- **BREAKOUT_BUY**: Enter on technical breakouts
- **PULLBACK_BUY**: Enter on pullbacks to trend lines
- **SUPPORT_BUY**: Buy at key support levels
- **RESISTANCE_SELL**: Sell at resistance levels

#### Momentum Indicators
- **RSI_OVERSOLD**: Buy when RSI < 30
- **RSI_OVERBOUGHT**: Sell when RSI > 70
- **MACD_CROSS**: Trade on MACD signal line crosses
- **VOLUME_CONFIRMATION**: Require volume confirmation for entries

### 9. Portfolio Optimization Actions

#### Diversification
- **SECTOR_LIMIT**: Enforce maximum sector concentration
- **CORRELATION_LIMIT**: Avoid highly correlated positions
- **GEOGRAPHIC_DIVERSIFY**: Add international exposure
- **SIZE_DIVERSIFY**: Mix large, mid, small cap stocks

#### Performance Enhancement
- **MOMENTUM_TILT**: Overweight momentum stocks
- **VALUE_TILT**: Overweight undervalued stocks
- **QUALITY_FILTER**: Only high-quality companies
- **VOLATILITY_TARGET**: Target specific portfolio volatility

### 10. Emergency Actions

#### Crisis Management
- **PANIC_SELL**: Emergency exit all positions
- **CIRCUIT_BREAKER**: Stop all trading activity
- **SAFE_HAVEN**: Move to treasury bonds/gold
- **LIQUIDITY_PRESERVE**: Only trade highly liquid securities

#### System Issues
- **API_FAILURE_MODE**: Simplified trading during API issues
- **MANUAL_OVERRIDE**: Flag positions for manual review
- **RISK_REDUCTION**: Immediate risk reduction measures
- **POSITION_FREEZE**: Hold all current positions

## Claude Response Format

Each Claude recommendation should include:

```json
{
  "action_type": "ADJUST_STOP_LOSS",
  "symbol": "AAPL",
  "parameters": {
    "new_stop_price": 145.50,
    "reason": "Technical support at $145.50, 3% below current price",
    "urgency": "normal",
    "time_frame": "end_of_day"
  },
  "confidence": 0.85,
  "alternative_action": "SELL_PARTIAL",
  "market_context": "Market showing increased volatility, protecting gains"
}
```

## Action Priority Levels

1. **IMMEDIATE**: Execute within minutes (emergency exits, stop losses hit)
2. **HIGH**: Execute within 1 hour (momentum changes, news reactions)
3. **NORMAL**: Execute within trading day (standard adjustments)
4. **LOW**: Execute when convenient (portfolio rebalancing)
5. **PLANNED**: Execute at specific time/condition (earnings plays, scale-ins)

## Risk Validation

Before executing any Claude action, the system should verify:
- Position size limits not exceeded
- Portfolio concentration rules followed
- Maximum daily/monthly loss limits respected
- Margin/cash requirements met
- Regulatory/tax implications considered 