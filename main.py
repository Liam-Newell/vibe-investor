#!/usr/bin/env python3
"""
Vibe Investor - AI-Driven Options Trading System
Main application entry point
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, time
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.scheduler import TradingScheduler
from src.services.claude_service import ClaudeService
from src.services.options_service import OptionsService
from src.services.portfolio_service import PortfolioService
from src.services.email_service import EmailService
from src.api.routes import trading, portfolio, claude_chat, health, email_test
from src.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global services
trading_scheduler: TradingScheduler = None
claude_service: ClaudeService = None
options_service: OptionsService = None
portfolio_service: PortfolioService = None
email_service: EmailService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global trading_scheduler, claude_service, options_service, portfolio_service, email_service
    
    logger.info("🚀 Starting Vibe Investor Options Trading System")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize services
        claude_service = ClaudeService()
        options_service = OptionsService()
        portfolio_service = PortfolioService()
        email_service = EmailService(claude_service=claude_service)
        
        # Initialize trading scheduler
        trading_scheduler = TradingScheduler(
            claude_service=claude_service,
            options_service=options_service,
            portfolio_service=portfolio_service,
            email_service=email_service
        )
        
        # Start paper trading mode
        if settings.PAPER_TRADING_ONLY:
            logger.info("📝 Starting in PAPER TRADING mode")
            await options_service.enable_paper_trading()
        
        # Schedule trading sessions
        await trading_scheduler.start()
        logger.info("⏰ Trading scheduler started")
        
        # Morning Claude session (if enabled and within schedule)
        if settings.CLAUDE_MORNING_ENABLED:
            await trading_scheduler.schedule_morning_session()
        
        # Evening Claude review (if enabled and within schedule)
        if settings.CLAUDE_EVENING_ENABLED:
            await trading_scheduler.schedule_evening_session()
        
        logger.info("🎯 Vibe Investor ready for options trading!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("🛑 Shutting down Vibe Investor")
        
        if trading_scheduler:
            await trading_scheduler.stop()
        
        await close_db()
        logger.info("👋 Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Vibe Investor",
    description="AI-Driven Options Trading System",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(claude_chat.router, prefix="/api/v1/claude", tags=["Claude AI"])
app.include_router(email_test.router, prefix="/api/v1/email", tags=["Email Testing"])

# Serve static files for dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard"""
    try:
        with open("static/dashboard.html") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
            <head><title>Vibe Investor</title></head>
            <body>
                <h1>🎯 Vibe Investor Options Trading System</h1>
                <p>Dashboard loading... Please check back in a moment.</p>
                <p>API Status: <a href="/api/v1/health">Health Check</a></p>
            </body>
        </html>
        """)


@app.get("/status")
async def system_status():
    """System status endpoint"""
    global trading_scheduler, claude_service, options_service, portfolio_service, email_service
    
    status = {
        "system": "Vibe Investor",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "paper_trading": settings.PAPER_TRADING_ONLY,
        "services": {
            "scheduler": trading_scheduler is not None and trading_scheduler.is_running(),
            "claude": claude_service is not None and await claude_service.health_check(),
            "options": options_service is not None,
            "portfolio": portfolio_service is not None,
            "email": email_service is not None,
        },
        "market": {
            "is_open": await is_market_open(),
            "next_session": await get_next_session_time(),
        },
        "claude_config": {
            "morning_enabled": settings.CLAUDE_MORNING_ENABLED,
            "evening_enabled": settings.CLAUDE_EVENING_ENABLED,
            "max_daily_queries": settings.CLAUDE_MAX_DAILY_QUERIES,
        }
    }
    
    return status


async def is_market_open() -> bool:
    """Check if market is currently open"""
    now = datetime.now()
    
    # Simple market hours check (9:30 AM - 4:00 PM ET, weekdays)
    if now.weekday() >= 5:  # Weekend
        return False
    
    market_open = time(9, 30)
    market_close = time(16, 0)
    current_time = now.time()
    
    return market_open <= current_time <= market_close


async def get_next_session_time() -> str:
    """Get next trading session time"""
    now = datetime.now()
    
    # Next morning session
    if settings.CLAUDE_MORNING_ENABLED:
        morning_time = datetime.strptime(settings.CLAUDE_MORNING_TIME, "%H:%M").time()
        next_morning = datetime.combine(now.date(), morning_time)
        
        if next_morning <= now:
            # Tomorrow morning
            from datetime import timedelta
            next_morning += timedelta(days=1)
        
        return f"Next morning session: {next_morning.strftime('%Y-%m-%d %H:%M')}"
    
    return "No scheduled sessions"


if __name__ == "__main__":
    """Run the application"""
    
    logger.info("🎯 Starting Vibe Investor Options Trading System")
    logger.info(f"📝 Paper Trading: {settings.PAPER_TRADING_ONLY}")
    logger.info(f"🌐 Dashboard: http://localhost:{settings.DASHBOARD_PORT}")
    
    uvicorn.run(
        "main:app",
        host=settings.DASHBOARD_HOST,
        port=settings.DASHBOARD_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    ) 