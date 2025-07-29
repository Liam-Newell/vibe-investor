"""
Trading API routes
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def trading_status():
    """Get trading system status"""
    return {
        "status": "paper_trading",
        "message": "Trading system ready for paper trading"
    }

@router.get("/positions")
async def get_positions():
    """Get current positions"""
    return {
        "positions": [],
        "total_count": 0
    } 