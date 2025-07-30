# Vibe Investor

## Project Overview
An intelligent options trading system that leverages Claude AI for volatility analysis, earnings timing, and strategic options selection. The system focuses on 6 concurrent options positions with 2-4 week holding periods, targeting realistic 20-30% annual returns through defined-risk strategies. Claude provides individual position analysis and portfolio-wide Greeks management.

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose installed
- Claude API key from Anthropic
- Email account for reports (Gmail, Outlook, or custom domain)

### Quick Setup (Under 5 Minutes!)

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/vibe-investor.git
cd vibe-investor
./setup.sh

# 2. Configure API keys
cp env.example .env
# Edit .env with your Claude API key and email settings

# 3. Start the system
docker-compose up -d

# 4. Access dashboard
open http://localhost:8080

# 5. View logs
./manage.sh logs
```

### Easy Management Commands

```bash
# System control
./manage.sh start          # Start the trading system
./manage.sh stop           # Stop the system
./manage.sh restart        # Restart everything
./manage.sh status         # Check system status

# Monitoring
./manage.sh logs           # View live logs
./manage.sh dashboard      # Open dashboard in browser
./manage.sh health         # System health check

# Maintenance
./manage.sh backup         # Create full system backup
./manage.sh update         # Update to latest version
```

### Configuration

Edit `.env` file with your settings:

```bash
# Required: Claude API key
CLAUDE_API_KEY=your_claude_api_key_here

# Required: Email settings (choose one option)
# Option 1: Use existing Gmail (easiest)
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # From myaccount.google.com/apppasswords
ALERT_EMAIL=liam-newell@hotmail.com

# Option 2: Custom domain (professional)
# SMTP_SERVER=smtp.zoho.com
# SMTP_USER=vibe@vibeinvestor.ca
# SMTP_PASSWORD=your-zoho-password

# Important: Always start with paper trading
PAPER_TRADING_ONLY=true
```

### Test Your Setup

```bash
# Test Claude integration
curl -X POST http://localhost:8080/api/v1/claude/test-json

# Test email delivery
curl -X POST http://localhost:8080/api/v1/email/test-morning-email

# Check system health
curl http://localhost:8080/health


```

## ✅ Achieved Goals

### Primary Goals
- [x] **Core Architecture**: FastAPI app with async services, PostgreSQL, Redis
- [x] **Claude AI Integration**: Structured JSON responses with individual position conversations
- [x] **Email Reports**: Beautiful morning/evening reports to liam-newell@hotmail.com
- [x] **Docker Deployment**: Complete containerized stack with one-command setup
- [x] **Options Data Models**: Complete Pydantic/SQLAlchemy models for positions, Greeks, strategies
- [x] **Paper Trading Framework**: Full autonomous execution environment with real position tracking
- [x] **Live Market Data Integration**: Yahoo Finance API for real-time pricing, option chains, and Greeks
- [x] **Autonomous Position Management**: Claude controls all position parameters (entry, exit, sizing, timing)
- [x] **Database Persistence**: SQLite-based position tracking across server restarts
- [x] **Real-time Dashboard**: Live P&L tracking with Yahoo Finance data updates
- [x] **Risk Management**: Portfolio limits, position tracking, circuit breakers
- [x] **Scheduling System**: Automated morning/evening Claude sessions
- [x] **Configuration Management**: Comprehensive .env setup with all options
- [x] **Management Tools**: Setup and management scripts for easy operation
- [ ] Achieve realistic 20-30% annual returns through AI-driven options strategies
- [ ] Maintain up to 6 concurrent options positions with defined risk management
- [ ] Focus on 2-4 week holding periods for better risk/reward asymmetry
- [ ] Comprehensive paper trading validation with options-specific metrics

### Secondary Goals
- [ ] Develop parallel traditional technical analysis system for performance comparison
- [ ] Create options income strategies (covered calls, protective puts) for portfolio enhancement
- [ ] Build comprehensive logging and performance analytics across all strategies
- [ ] Create unified dashboard monitoring all parallel trading systems
- [ ] Implement backtesting capabilities for strategy validation and optimization

## 🔧 Technical Implementation Status

### ✅ Completed Components

#### Core Application
- [x] **Language**: Python 3.11+ (chosen for financial libraries and API integration)
- [x] **Framework**: FastAPI for API endpoints and web dashboard
- [x] **Async Processing**: asyncio for concurrent market data processing
- [x] **Task Scheduling**: APScheduler for timed Claude queries and market checks

#### AI & External APIs
- [x] **Claude Integration**: anthropic-sdk for AI decision making with structured JSON
- [x] **HTTP Client**: httpx for API calls
- [x] **Rate Limiting**: Built into Claude service

#### Data Storage
- [x] **Database**: PostgreSQL for structured trading data
- [x] **ORM**: SQLAlchemy for database operations
- [x] **Caching**: Redis for real-time market data and session storage
- [ ] **Time Series**: TimescaleDB extension for historical price data

#### Infrastructure & Monitoring
- [x] **Deployment**: Docker Compose for simple home server deployment
- [x] **Web Dashboard**: FastAPI-based browser interface for monitoring
- [x] **Database**: PostgreSQL + Redis containers
- [x] **Monitoring**: Built-in performance dashboard and email alerts
- [x] **Logging**: Centralized logging with log rotation
- [x] **Notifications**: Email alerts system implemented
- [x] **Backup**: Automated database backups and configuration snapshots

#### API Endpoints & Services
- [x] **Health Checks**: System status monitoring
- [x] **Claude Testing**: JSON response validation endpoints
- [x] **Email Testing**: Morning/evening report testing
- [x] **Service Integration**: All core services properly initialized

#### Email System
- [x] **Multiple Providers**: Gmail, Outlook, Zoho, custom domain support
- [x] **Beautiful Reports**: Claude-generated HTML content
- [x] **Morning Reports**: Pre-market analysis and opportunities
- [x] **Evening Reports**: Performance summary and position updates
- [x] **Professional Sender**: Support for custom domain (vibe@vibeinvestor.ca)

#### Security & Configuration
- [x] **API Key Management**: Secure environment variable handling
- [x] **Configuration System**: Comprehensive .env template with all options
- [x] **Docker Security**: Network isolation and health checks
- [x] **Backup Encryption**: Optional GPG encryption for backup files
- [x] **Audit Logging**: Complete trail of all decisions and actions

### ⏳ Remaining Tasks

#### Financial & Trading Libraries
- [x] **Market Data**: yfinance integration with real-time pricing and option chains
- [x] **Data Analysis**: pandas, numpy for financial calculations (fully connected)
- [x] **Live Greeks Calculation**: Real delta, theta, vega from option chain data
- [ ] **Broker Integration**: ib_insync (IBKR) or questrade-api (Questtrade)
- [ ] **Technical Analysis**: TA-Lib or pandas-ta for indicators

#### Trading System
- [x] **Live Market Data**: Real-time options pricing and Greeks calculation from Yahoo Finance
- [x] **Options Pricing**: Live option chain data with real Greeks calculations
- [x] **Autonomous Execution**: Claude-controlled position creation with database persistence
- [x] **Position Monitoring**: Real-time P&L tracking and exit criteria evaluation
- [ ] **Traditional System**: Basic technical analysis for performance comparison
- [ ] **Backtesting**: Historical strategy validation framework
- [ ] **Live Trading**: Broker API connection and execution (currently paper trading only)

#### Advanced Features
- [x] **Risk Metrics**: Dynamic confidence thresholds and performance-based adjustments
- [x] **Real-time Dashboard**: Live position tracking with Yahoo Finance data
- [x] **Mobile-Responsive UI**: Dashboard works on all devices
- [ ] **Advanced Risk Metrics**: VaR, correlation analysis, stress testing
- [ ] **Production Deployment**: SSL, domain setup, monitoring alerts
- [ ] **Performance Analytics**: Advanced reporting and metrics

## Requirements

### Functional Requirements

#### ✅ Implemented
- [x] **Morning Claude Strategy**: Pre-market AI analysis for options selection and daily strategy
- [x] **Evening Claude Review**: Post-market AI analysis and strategy adjustment
- [x] **Autonomous Position Management**: Max 6 concurrent positions with full Claude control
- [x] **Live Market Data Integration**: Yahoo Finance API for real-time pricing and option chains
- [x] **Database Schema**: All tables for positions, decisions, parameters, market data
- [x] **Claude Conversation Management**: Individual threads per position capability
- [x] **Email Reporting**: Daily summaries and trade confirmations with performance tracking
- [x] **Real-time Position Tracking**: Live P&L calculation and exit criteria monitoring
- [x] **Autonomous Trade Execution**: Claude creates positions with zero human intervention
- [x] **Dynamic Risk Management**: Performance-based confidence and position sizing

#### ⏳ In Progress / Planned
- [ ] **Broker API Integration**: IBKR/Questtrade API for live trade execution
- [ ] **Traditional Benchmark System**: Basic technical analysis for performance comparison
- [ ] **Options Income System**: Covered calls, protective puts, and income-generating strategies
- [ ] **Advanced Analytics**: Backtesting and strategy optimization tools

### Non-Functional Requirements

#### Performance
- [x] Database query optimization framework ready
- [x] Claude API rate limiting compliance (max queries per day)
- [ ] Market data processing latency < 100ms
- [ ] Trade execution response time < 2 seconds
- [ ] System uptime 99.9% during market hours

#### Security
- [x] Secure API key management and encryption
- [x] Data encryption for sensitive financial information
- [x] Audit logging for all trading decisions and executions
- [x] Secure storage of conversation histories
- [ ] Broker API authentication and session management

#### Reliability
- [x] Data backup and recovery procedures
- [x] Error handling for API failures and network issues
- [x] Graceful degradation when external services are unavailable
- [ ] Automatic failover for critical system components
- [ ] Transaction rollback capabilities for failed trades

## Technology Stack

### ✅ Core Technology Implemented
- **Language**: Python 3.11+
- **Web Framework**: FastAPI with asyncio
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for real-time data and sessions
- **AI Integration**: Anthropic Claude API (claude-3-sonnet-20240229)
- **Scheduling**: APScheduler for timed tasks
- **Email**: aiosmtplib with Jinja2 templates
- **Deployment**: Docker Compose for easy home server setup
- **Monitoring**: Structured logging with health checks

### 📦 Dependencies Included
```python
# All major dependencies installed in requirements.txt:
fastapi==0.104.1
anthropic==0.7.8
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
aiosmtplib==3.0.1
pandas==2.1.4
numpy==1.25.2
py_vollib==1.0.1  # Options pricing
ib_insync==0.9.86  # IBKR integration
apscheduler==3.10.4
```

## 📧 Email Reports

**✅ FULLY IMPLEMENTED!** Get beautiful, AI-generated trading reports delivered to your inbox:

### 🌅 Morning Reports (8:00 AM)
- Claude's options opportunities for the day
- Market analysis and volatility outlook  
- Specific trade recommendations with time horizons
- Portfolio snapshot and risk assessment

### 🌆 Evening Reports (5:00 PM)
- Daily performance with P&L breakdown
- Individual position updates and Greeks
- Trades executed with Claude's reasoning
- Tomorrow's action items and market outlook

**Setup Options**: 
- **🚀 Quick Start** (use existing email): [QUICK_EMAIL_START.md](QUICK_EMAIL_START.md) 
- **💎 Professional** (custom domain): [SIMPLE_EMAIL_SETUP.md](SIMPLE_EMAIL_SETUP.md)
- **📖 Full Guide**: [EMAIL_SETUP.md](EMAIL_SETUP.md)

## 🤖 Claude AI Integration

**100% Autonomous Trading Process with Web Search:**
1. **Claude Autonomous Selection**: AI independently picks stocks/options using built-in web search tool
2. **Live Data Validation**: System searches real-time data for Claude's autonomous picks only
3. **Final Autonomous Decision**: Claude reviews live market conditions and confirms/modifies its own opportunities
4. **Autonomous Execution**: Dynamic filtering and automatic position creation

**Key Features:**
- [x] Complete Claude autonomy - no human proposals or input
- [x] **Built-in web search tool integration** for comprehensive market research
- [x] Intelligent stock selection based on Claude's web research and market knowledge
- [x] Targeted live data search (only for Claude's picks - efficient!)
- [x] Real-time price validation before execution
- [x] Adaptive strategy based on market conditions and portfolio performance
- [x] Research-backed confidence thresholds by strategy type
- [x] **Web search tool usage**: 5 searches for initial picks, 3 for final decisions, 4 for evening review

## 🔄 Autonomous Trading Flow

### **Morning Strategy Session (6:00 AM EST)**
1. **Portfolio Assessment**
   ```python
   # Real portfolio data from database
   portfolio = await options_service.get_portfolio_summary()
   current_positions = await options_service.get_active_positions()
   ```

2. **Claude's Autonomous Stock Selection**
   ```python
   # Claude independently chooses symbols and strategies
   initial_picks = await claude_service._get_claude_initial_picks(portfolio, market_context)
   # Returns: [{"symbol": "AAPL", "strategy_type": "long_call", "initial_confidence": 0.85}, ...]
   ```

3. **Live Market Data Validation**
   ```python
   # Only search data for Claude's autonomous picks
   symbols = [pick["symbol"] for pick in initial_picks]
   live_data = await web_search.search_stock_data(symbols)
   market_data = await market_service.get_option_chains(symbols)
   ```

4. **Claude's Final Autonomous Decision**
   ```python
   # Claude reviews live data for its own selected symbols
   final_decisions = await claude_service._get_claude_final_decision(
       initial_picks, live_data, market_data, portfolio
   )
   # Returns: Complete position specifications with all parameters
   ```

5. **Automatic Position Creation**
   ```python
   # System automatically creates positions based on Claude's specifications
   for opportunity in final_decisions:
       if opportunity.confidence >= dynamic_threshold:
           position = await options_service.create_position_from_opportunity(opportunity)
           await database.save_position(position)
   ```

### **Continuous Position Monitoring**
- **Real-time P&L tracking** with Yahoo Finance data every 5 minutes
- **Automatic exit criteria evaluation** based on Claude's original specifications
- **Dynamic risk adjustment** based on portfolio performance history

### **Evening Review Session (6:00 PM EST)**
1. **Performance Analysis**: Real portfolio performance vs. Claude's expectations
2. **Position Adjustments**: Claude can modify stop losses and profit targets
3. **Next Day Strategy**: Claude adjusts approach based on performance feedback
4. **Web Research**: Claude searches for after-hours news and tomorrow's market catalysts

## 🔍 Web Search Tool Integration

### **Built-in Claude Web Search**
The system uses Claude's native web search tool (`web_search_20250305`) for comprehensive market research:

```python
# Web search tool configuration
tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]
```

### **Web Search Usage by Session**
- **Morning Strategy**: 5 web searches for initial stock/options research
- **Final Decision**: 3 web searches for live data validation
- **Evening Review**: 4 web searches for after-hours analysis
- **Position Analysis**: 2 web searches for individual position research
- **Emergency Analysis**: 3 web searches for urgent market research

### **Research Topics**
Claude searches for:
- Current market sentiment and trends
- Recent earnings announcements and analyst ratings
- Technical analysis and support/resistance levels
- Options flow data and unusual activity
- Sector rotation and market catalysts
- Breaking news affecting positions
- After-hours market developments

### **Test Web Search Integration**
```bash
# Test Claude's web search capabilities
curl -X POST http://localhost:8080/api/v1/trading/test-web-search-integration
```

## 📊 Claude's Decision-Making Framework

### **Risk-Weighted Decision Process**

#### **1. Performance-Based Confidence Adjustment**
```python
def calculate_dynamic_confidence_threshold(portfolio_performance):
    base_threshold = 0.70  # Base 70% confidence required
    
    # Adjust based on recent performance
    if portfolio_performance.current_streak >= 3:
        # Hot streak: slightly more aggressive
        return max(0.65, base_threshold - 0.05)
    elif portfolio_performance.consecutive_losses >= 2:
        # Losing streak: more conservative
        return min(0.80, base_threshold + 0.10)
    
    return base_threshold
```

#### **2. Position Sizing Based on Performance**
```python
def calculate_position_size_multiplier(portfolio_performance):
    base_size = 2.5  # Base 2.5% of portfolio per position
    
    # Scale based on recent performance
    if portfolio_performance.recent_win_rate > 0.75:
        return min(3.5, base_size * 1.4)  # Max 3.5% when hot
    elif portfolio_performance.recent_win_rate < 0.40:
        return max(1.5, base_size * 0.6)  # Min 1.5% when cold
    
    return base_size
```

#### **3. Strategy-Specific Confidence Thresholds**
```python
strategy_confidence_requirements = {
    "long_call": 0.75,      # Bullish directional bets need high confidence
    "long_put": 0.75,       # Bearish directional bets need high confidence  
    "iron_condor": 0.65,    # Range-bound strategies, lower confidence OK
    "credit_spread": 0.70,  # Income strategies, moderate confidence
    "put_spread": 0.70,     # Defined risk spreads, moderate confidence
}
```

### **Claude's Parameter Control**

**Claude has full autonomous control over:**
- ✅ **Entry Prices**: Exact premium costs and position sizing
- ✅ **Stop Losses**: Maximum acceptable loss per position  
- ✅ **Profit Targets**: Specific exit prices for profit taking
- ✅ **Expiry Selection**: Optimal time decay balance (typically 2-6 weeks)
- ✅ **Strike Prices**: Based on technical analysis and volatility
- ✅ **Strategy Types**: Calls, puts, spreads, condors based on market outlook
- ✅ **Position Sizing**: Dynamic scaling based on confidence and performance
- ✅ **Exit Timing**: When to close positions early vs. hold to expiry

### **Market Data Integration**

**Live Data Sources (Zero Mock Data):**
```python
# Real market data from Yahoo Finance
current_prices = await yfinance.get_current_prices(symbols)
option_chains = await yfinance.get_option_chains(symbols, expirations)
market_sentiment = await market_service.analyze_sentiment()
vix_level = await yfinance.get_vix_current()

# Real portfolio data from database  
portfolio_summary = await database.get_portfolio_summary()
current_positions = await database.get_active_positions()
performance_history = await database.get_performance_metrics()
```

**Data Flow:**
1. **Morning**: Live market data → Claude analysis → Position creation
2. **Intraday**: Live price updates → P&L recalculation → Exit monitoring  
3. **Evening**: Live performance data → Claude review → Strategy adjustment

## 🚀 Current Production Status

### **Fully Operational Autonomous Trading System**

**✅ Ready for Deployment:**
The system is production-ready for paper trading with complete autonomous functionality:

```bash
# Start the system
docker-compose up -d

# Access dashboard  
open http://localhost:8080/

# View live trading positions
curl http://localhost:8080/api/live-update
```

**What Happens When You Deploy:**

1. **6:00 AM EST**: Claude autonomously analyzes markets and creates positions
2. **Throughout Day**: Live Yahoo Finance data updates position values in real-time  
3. **6:00 PM EST**: Claude reviews performance and adjusts strategy
4. **Email Reports**: Morning opportunities and evening performance summaries

### **Live Example Output**

**Morning (Claude Creates Positions):**
```json
{
  "claude_decisions": [
    {
      "symbol": "AAPL",
      "strategy": "Long Call",
      "entry_cost": 2750.0,
      "profit_target": 3500.0,
      "stop_loss": 2200.0,
      "expiry": "2025-09-19",
      "confidence": 0.82,
      "rationale": "Strong earnings momentum, technical breakout"
    }
  ],
  "positions_created": 3,
  "total_capital_deployed": "$7,800"
}
```

**Evening (Live P&L Tracking):**
```json
{
  "portfolio_summary": {
    "total_value": 99986.31,
    "unrealized_pnl": -13.69,
    "open_positions": 3,
    "current_streak": 0
  },
  "live_positions": [
    {
      "symbol": "AAPL",
      "entry_cost": 2750.0,
      "current_value": 2732.0,
      "unrealized_pnl": -18.0,
      "days_held": 1
    }
  ]
}
```

### **Zero Mock Data Verification**

**✅ All Real Data Sources:**
- Portfolio values from SQLite database
- Position tracking with persistent storage
- Live market prices from Yahoo Finance API
- Real option chain data and Greeks calculations
- Actual P&L calculations based on market movements

**✅ Zero Human Intervention Required:**
- Claude picks all symbols autonomously
- Claude sets all position parameters (entry, exit, sizing)
- Automatic position creation and tracking
- Self-adjusting risk management based on performance

### **Current Limitations (Paper Trading Only)**
- **No Broker Connection**: Positions are tracked in database only
- **Simulated Execution**: No actual money at risk
- **Manual Live Trading**: Requires broker API integration for real trades

**Next Step for Live Trading:**
```python
# Add broker integration (IBKR or Questtrade)
BROKER_API_KEY=your_broker_key
LIVE_TRADING_ENABLED=true  # Currently: PAPER_TRADING_ONLY=true
```

## Complete Docker Compose Stack

✅ **FULLY CONFIGURED** - Production-ready deployment:

```yaml
# docker-compose.yml includes:
services:
  vibe-investor:     # Main FastAPI application
  postgres:          # PostgreSQL database  
  redis:            # Caching and sessions
  backup:           # Automated daily backups
  monitoring:       # Optional Grafana dashboard
  proxy:            # Optional SSL/domain setup
```

### Key Features
- **Health checks**: All services monitored with restart policies
- **Volume persistence**: Data, logs, backups, and config preserved
- **Network isolation**: Custom bridge network for security
- **Environment configuration**: All settings via `.env` file
- **Easy management**: Simple start/stop/logs commands via `manage.sh`

## Success Metrics & Validation

### Paper Trading Phase (✅ Ready)
- [x] **System Architecture**: Complete technical foundation 
- [x] **Claude Integration**: AI decision-making with structured responses
- [x] **Email Reports**: Automated beautiful reports twice daily
- [x] **Risk Management**: Portfolio limits and position tracking
- [ ] **Minimum duration**: 60 days successful operation
- [ ] **Performance target**: Outperform SPY benchmark
- [ ] **Risk limits**: <10% maximum drawdown
- [ ] **Reliability**: >95% system uptime and order fill accuracy
- [ ] **AI effectiveness**: Positive Sharpe ratio for Claude decisions

### Live Trading Phase (Future)
- [ ] **Annual return target**: 20-30% (realistic and achievable)
- [ ] **Risk management**: Maintain position limits and portfolio Greeks
- [ ] **Technology reliability**: 99%+ uptime for production system
- [ ] **Decision accuracy**: Track Claude's recommendation success rate

## Development Timeline

### ✅ Phase 1: Foundation Complete (Weeks 1-4)
- [x] Set up Python development environment and dependencies
- [x] Implement Claude API integration for morning/evening sessions
- [x] Create paper trading system framework
- [x] Integrate market data APIs structure
- [x] Create database schema for tracking all systems
- [x] Build email reporting system
- [x] Docker deployment configuration

### ⏳ Phase 2: Market Integration (Weeks 5-8) 
- [x] Develop Claude morning strategy session system
- [x] Build Claude evening review and learning system
- [ ] Build technical execution engine with entry/exit logic
- [ ] Create traditional benchmark system for comparison
- [ ] Build basic options income strategies
- [ ] Connect to live market data feeds

### 🔄 Phase 3: Testing & Optimization (Weeks 9-12)
- [ ] Extensive paper trading validation (minimum 2-3 months)
- [ ] A/B testing between AI-driven vs traditional strategies
- [ ] Performance analytics and strategy refinement
- [ ] Risk management system improvements
- [ ] Multi-system coordination and conflict resolution

### 🎯 Phase 4: Live Trading (Months 4-6)
- [ ] Start with minimal live capital (5-10% of intended amount)
- [ ] Gradually increase position sizes based on performance
- [ ] Continuous monitoring and strategy adjustment
- [ ] Scale successful systems, disable underperforming ones

### ⚠️ Important: No live capital until paper trading proves profitability over 60+ days

## What Works Right Now

✅ **Ready to Test:**
```bash
# Start the system
docker-compose up -d

# Test Claude AI integration  
curl -X POST http://localhost:8080/api/v1/claude/test-json

# Test email delivery
curl -X POST http://localhost:8080/api/v1/email/test-morning-email

# View system status
curl http://localhost:8080/health
```

✅ **Architecture Complete:**
- FastAPI web application with all routes
- Claude service with structured JSON responses
- Email service with beautiful HTML reports
- Complete Docker deployment stack
- PostgreSQL database with options trading schema
- Redis caching and session management
- Automated backup and monitoring systems
- Management scripts for easy operation

⏳ **Next Steps for Live Trading:**
1. Connect to IBKR or Questtrade API for market data
2. Implement real-time options pricing and Greeks
3. Add traditional technical analysis for comparison
4. 60+ days of paper trading validation
5. Gradual transition to live capital

## Why Docker Compose?
✅ **Single Command Deployment**: `docker-compose up -d` starts everything  
✅ **Complete Isolation**: No conflicts with other software  
✅ **Easy Updates**: `./manage.sh update` handles everything  
✅ **Portable**: Move to any server by copying files  
✅ **Backup Friendly**: `./manage.sh backup` creates complete snapshots  
✅ **Development/Production**: Same setup works everywhere  
✅ **Browser Access**: Dashboard at `http://localhost:8080`  
✅ **Email Alerts**: Automatic notifications for important events  

## Contributing
Guidelines for contributing to the project.

## License
[Specify the license for the project]

---

*This document reflects the current implementation status. All core architecture is complete and ready for market data integration.* 