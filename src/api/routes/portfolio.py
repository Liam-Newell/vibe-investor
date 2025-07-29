"""
Portfolio API routes
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/summary")
async def portfolio_summary():
    """Get portfolio summary"""
    return {
        "total_value": 100000.0,
        "cash_balance": 100000.0,
        "open_positions": 0,
        "total_pnl": 0.0
    } 