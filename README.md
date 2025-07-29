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
- [x] **Paper Trading Framework**: Mock execution environment for validation
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
- [ ] **Broker Integration**: ib_insync (IBKR) or questrade-api (Questtrade)
- [ ] **Market Data**: yfinance, alpha_vantage, or polygon.io integration
- [ ] **Data Analysis**: pandas, numpy for financial calculations (installed but not connected)
- [ ] **Technical Analysis**: TA-Lib or pandas-ta for indicators

#### Trading System
- [ ] **Live Market Data**: Real-time options pricing and Greeks calculation
- [ ] **Options Pricing**: Black-Scholes and Greeks calculations implementation
- [ ] **Traditional System**: Basic technical analysis for performance comparison
- [ ] **Backtesting**: Historical strategy validation framework
- [ ] **Live Trading**: Broker API connection and execution

#### Advanced Features
- [ ] **Advanced Risk Metrics**: VaR, correlation analysis, stress testing
- [ ] **Production Deployment**: SSL, domain setup, monitoring alerts
- [ ] **Mobile Dashboard**: Responsive UI improvements
- [ ] **Performance Analytics**: Advanced reporting and metrics

## Requirements

### Functional Requirements

#### ✅ Implemented
- [x] **Morning Claude Strategy**: Pre-market AI analysis for options selection and daily strategy
- [x] **Evening Claude Review**: Post-market AI analysis and strategy adjustment
- [x] **Position management system**: Max 6 concurrent positions framework
- [x] **Database Schema**: All tables for positions, decisions, parameters, market data
- [x] **Claude Conversation Management**: Individual threads per position capability
- [x] **Email Reporting**: Daily summaries and trade confirmations

#### ⏳ In Progress / Planned
- [ ] **Technical Execution Engine**: Real-time technical indicators for trade entry/exit timing
- [ ] IBKR/Questtrade API integration for automated trade execution
- [ ] Real-time market data integration and monitoring
- [ ] **Traditional Benchmark System**: Basic technical analysis for performance comparison
- [ ] **Options Income System**: Covered calls, protective puts, and income-generating strategies

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

### Claude AI Integration
Claude now returns **structured JSON data** for reliable processing:
- **🤖 Integration Guide**: [CLAUDE_INTEGRATION_GUIDE.md](CLAUDE_INTEGRATION_GUIDE.md)
- **Test endpoint**: `/api/v1/claude/test-json`

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