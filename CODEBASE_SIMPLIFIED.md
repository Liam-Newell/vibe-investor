# 🗂️ Simplified Codebase Guide

## 📁 **Core Structure (What You Need to Know)**

### **🚀 Main Entry Points**
- `main.py` - FastAPI app startup
- `docker-compose.yml` - Container orchestration
- `requirements.txt` - Dependencies

### **📊 Dashboard & Frontend**
- `templates/dashboard.html` - Main trading dashboard
- `static/` - CSS, JS, images

### **🔧 Core Services (The Important Stuff)**

#### **1. Trading Logic** (`src/services/options_service.py`)
- **What it does**: Creates positions, manages portfolio, executes trades
- **Key functions**:
  - `create_position_from_opportunity()` - Creates positions from Claude picks
  - `execute_approved_opportunities()` - Executes approved trades
  - `update_position_values()` - Updates position P&L

#### **2. Claude AI** (`src/services/claude_service.py`)
- **What it does**: Claude picks stocks and makes trading decisions
- **Key functions**:
  - `morning_strategy_session()` - Morning stock picking
  - `evening_review_session()` - Evening position review

#### **3. Market Data** (`src/services/market_data_service.py`)
- **What it does**: Gets live stock prices and option chains
- **Key functions**:
  - `get_option_chain()` - Gets option prices
  - `get_current_price()` - Gets stock prices

#### **4. Email Notifications** (`src/services/email_service.py`)
- **What it does**: Sends morning/evening reports
- **Key functions**:
  - `send_morning_report()` - Morning strategy email
  - `send_evening_report()` - Evening review email

### **⚙️ Configuration & Scheduling**
- `src/core/config.py` - All settings (API keys, times, etc.)
- `src/core/scheduler.py` - Runs Claude sessions at scheduled times

### **🗄️ Database & Models**
- `src/models/options.py` - Data structures (positions, contracts)
- `src/core/database.py` - Database connection

## 🎯 **Quick Debugging Guide**

### **"Positions Not Showing"**
1. Check `src/services/options_service.py` - `create_position_from_opportunity()`
2. Look for field validation errors
3. Check logs for "Missing required field" errors

### **"Claude Not Running"**
1. Check `src/core/scheduler.py` - `_morning_session()`
2. Verify `CLAUDE_MORNING_ENABLED = True` in config
3. Check timezone settings

### **"No Email Reports"**
1. Check `src/core/config.py` - `EMAIL_ENABLED = True`
2. Check `src/services/email_service.py` - SMTP settings
3. Verify email credentials in environment

### **"Dashboard Not Loading"**
1. Check `src/api/routes/dashboard.py` - `/api/live-update`
2. Verify port 8000 is exposed in `docker-compose.yml`
3. Check browser console for JavaScript errors

## 🔧 **Common Fixes**

### **Field Mismatch Errors**
```python
# In src/services/options_service.py
# BEFORE: Strict validation
required_fields = ['symbol', 'strategy_type', 'confidence', 'target_return', 'max_risk']

# AFTER: Flexible with defaults
required_fields = ['symbol', 'strategy_type', 'confidence']
if 'target_return' not in opportunity:
    opportunity['target_return'] = opportunity.get('profit_target', 500.0)
```

### **Option Contract Errors**
```python
# In src/services/options_service.py
# BEFORE: Wrong field names
OptionContract(strike_price=450, expiration_date=date)

# AFTER: Correct field names
OptionContract(strike=450, expiration=date, symbol="AAPL", quantity=1)
```

### **Email Not Working**
```python
# In src/core/config.py
EMAIL_ENABLED: bool = Field(True)  # Make sure this is True
```

## 📋 **Key Files for Each Feature**

### **Manual Strategy Execution**
- `src/api/routes/trading.py` - `/run-morning-strategy` endpoint
- `templates/dashboard.html` - "Run Claude Strategy" button

### **Portfolio Reset**
- `src/api/routes/trading.py` - `/reset-portfolio` endpoint
- `templates/dashboard.html` - "Reset Portfolio" button

### **Position Display**
- `src/api/routes/dashboard.py` - `/api/live-update` endpoint
- `templates/dashboard.html` - Position display logic

### **Scheduled Sessions**
- `src/core/scheduler.py` - Morning/evening session scheduling
- `src/services/claude_service.py` - Claude strategy logic

## 🚀 **Quick Start Commands**

```bash
# Start the system
docker compose up -d

# Check logs
docker compose logs -f vibe-investor

# Test manual strategy
curl -X POST http://localhost:8000/api/v1/trading/run-morning-strategy

# Reset portfolio
curl -X POST http://localhost:8000/api/v1/trading/reset-portfolio

# Check dashboard
open http://localhost:8000/dashboard
```

## 🎯 **What Each Service Does**

| Service | Purpose | Key File |
|---------|---------|----------|
| **Options Service** | Creates/executes positions | `src/services/options_service.py` |
| **Claude Service** | AI trading decisions | `src/services/claude_service.py` |
| **Market Data** | Live prices & options | `src/services/market_data_service.py` |
| **Email Service** | Morning/evening reports | `src/services/email_service.py` |
| **Scheduler** | Runs sessions on time | `src/core/scheduler.py` |
| **Dashboard** | Web interface | `templates/dashboard.html` |

## 🔍 **Debugging Checklist**

- [ ] **Positions not showing**: Check field validation in `options_service.py`
- [ ] **Claude not running**: Check scheduler and config settings
- [ ] **No emails**: Check `EMAIL_ENABLED = True` in config
- [ ] **Dashboard errors**: Check browser console and API endpoints
- [ ] **Port issues**: Check `docker-compose.yml` port mappings

---

**🎯 This simplified structure makes it easy to find and fix issues quickly!** 