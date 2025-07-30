#!/usr/bin/env python3
"""
Vibe Investor - AI-Driven Options Trading Platform
Main FastAPI application entry point
"""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.core.config import settings
from src.api.routes import health, portfolio, trading, claude_chat, email_test, dashboard
from src.core.database import init_database
from src.core.scheduler import TradingScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Vibe Investor",
    description="AI-Driven Options Trading Platform with Claude Integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading"])
app.include_router(claude_chat.router, prefix="/api/v1/claude", tags=["Claude AI"])
app.include_router(email_test.router, prefix="/api/v1/email", tags=["Email"])

# Include dashboard routes (main page)
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# Initialize scheduler
scheduler = None

@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler on app startup"""
    global scheduler
    
    logger.info("🚀 Starting Vibe Investor application...")
    
    # Initialize database
    await init_database()
    logger.info("✅ Database initialized")
    
    # Start trading scheduler
    scheduler = TradingScheduler()
    await scheduler.start()
    logger.info("✅ Trading scheduler started")
    
    logger.info("🎉 Vibe Investor is ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown"""
    global scheduler
    
    logger.info("🛑 Shutting down Vibe Investor...")
    
    if scheduler:
        await scheduler.stop()
        logger.info("✅ Trading scheduler stopped")
    
    logger.info("👋 Vibe Investor shutdown complete")

@app.get("/")
async def root():
    """Root endpoint redirects to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard/")

if __name__ == "__main__":
    logger.info(f"🔥 Starting server on port {settings.PORT}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    ) 