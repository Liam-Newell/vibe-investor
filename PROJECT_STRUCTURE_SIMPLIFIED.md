# 🏗️ Simplified Project Structure

## 📁 **Root Level (What You See)**
```
vibe-investor/
├── 🚀 main.py                    # FastAPI app startup
├── 🐳 docker-compose.yml         # Container setup
├── 📋 requirements.txt           # Python dependencies
├── 📊 templates/dashboard.html   # Main dashboard
├── 📧 test_email_fix.py          # Email test script
└── 📚 README.md                  # Project overview
```

## 🔧 **Core Services (The Engine)**
```
src/
├── services/
│   ├── 🎯 options_service.py     # Creates/executes positions
│   ├── 🤖 claude_service.py      # AI trading decisions
│   ├── 📡 market_data_service.py # Live stock prices
│   └── 📧 email_service.py       # Morning/evening reports
├── core/
│   ├── ⚙️ config.py              # All settings
│   ├── ⏰ scheduler.py            # Runs sessions on time
│   └── 🗄️ database.py            # Database connection
├── api/routes/
│   ├── 📊 dashboard.py           # Dashboard API
│   └── 🎯 trading.py             # Trading endpoints
└── models/
    └── 📋 options.py             # Data structures
```

## 🎯 **What Each File Does**

### **🚀 Startup & Configuration**
| File | Purpose |
|------|---------|
| `main.py` | Starts the FastAPI web server |
| `docker-compose.yml` | Runs everything in containers |
| `src/core/config.py` | All settings (API keys, times, etc.) |

### **🤖 AI & Trading Logic**
| File | Purpose |
|------|---------|
| `src/services/claude_service.py` | Claude picks stocks and makes decisions |
| `src/services/options_service.py` | Creates and manages trading positions |
| `src/services/market_data_service.py` | Gets live stock prices and options |

### **📊 User Interface**
| File | Purpose |
|------|---------|
| `templates/dashboard.html` | Main trading dashboard |
| `src/api/routes/dashboard.py` | Dashboard data API |
| `src/api/routes/trading.py` | Manual strategy execution |

### **⏰ Scheduling & Automation**
| File | Purpose |
|------|---------|
| `src/core/scheduler.py` | Runs Claude sessions at 9:46 AM and 5:00 PM |
| `src/services/email_service.py` | Sends morning/evening email reports |

## 🔍 **Quick Navigation Guide**

### **"I want to change trading logic"**
→ `src/services/options_service.py`

### **"I want to modify Claude's behavior"**
→ `src/services/claude_service.py`

### **"I want to change the dashboard"**
→ `templates/dashboard.html`

### **"I want to change settings"**
→ `src/core/config.py`

### **"I want to change when Claude runs"**
→ `src/core/scheduler.py`

### **"I want to modify email reports"**
→ `src/services/email_service.py`

## 🚀 **Key Endpoints**

| Endpoint | Purpose | File |
|----------|---------|------|
| `GET /dashboard` | Main dashboard | `templates/dashboard.html` |
| `GET /api/live-update` | Dashboard data | `src/api/routes/dashboard.py` |
| `POST /api/v1/trading/run-morning-strategy` | Manual strategy | `src/api/routes/trading.py` |
| `POST /api/v1/trading/reset-portfolio` | Reset portfolio | `src/api/routes/trading.py` |

## 🔧 **Common Tasks**

### **Add a New Strategy Type**
1. Add to `src/models/options.py` - StrategyType enum
2. Add logic to `src/services/options_service.py` - `_create_real_option_contracts()`
3. Test with manual strategy execution

### **Change Email Content**
1. Modify `src/services/email_service.py` - `_generate_morning_report_html()`
2. Test with `test_email_fix.py`

### **Add Dashboard Feature**
1. Add to `templates/dashboard.html` - Frontend
2. Add to `src/api/routes/dashboard.py` - Backend API
3. Test via browser

### **Change Claude's Behavior**
1. Modify `src/services/claude_service.py` - Prompts and logic
2. Test with manual strategy execution

## 📋 **Debugging Checklist**

### **System Won't Start**
- [ ] Check `docker-compose.yml` port mappings
- [ ] Verify `requirements.txt` dependencies
- [ ] Check `src/core/config.py` settings

### **Dashboard Not Working**
- [ ] Check `templates/dashboard.html` JavaScript
- [ ] Verify `src/api/routes/dashboard.py` endpoints
- [ ] Check browser console for errors

### **Trading Not Working**
- [ ] Check `src/services/options_service.py` field validation
- [ ] Verify `src/services/claude_service.py` Claude responses
- [ ] Check logs for Pydantic errors

### **Emails Not Sending**
- [ ] Check `src/core/config.py` - `EMAIL_ENABLED = True`
- [ ] Verify email credentials in environment
- [ ] Test with `test_email_fix.py`

### **Scheduled Sessions Not Running**
- [ ] Check `src/core/scheduler.py` - Session scheduling
- [ ] Verify timezone settings in config
- [ ] Check `CLAUDE_MORNING_ENABLED = True`

## 🎯 **Key Configuration Settings**

```python
# src/core/config.py - Key settings to check
CLAUDE_API_KEY = "your-api-key"
CLAUDE_MORNING_ENABLED = True
CLAUDE_MORNING_TIME = "09:46"
EMAIL_ENABLED = True
AUTO_EXECUTE_TRADES = True
PAPER_TRADING_ONLY = True
```

---

**🎯 This simplified structure makes it easy to find what you need and fix issues quickly!** 