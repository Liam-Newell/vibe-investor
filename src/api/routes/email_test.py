"""
Email Test API routes
For testing email configuration
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from src.services.email_service import EmailService
from src.services.claude_service import ClaudeService
from src.models.options import PortfolioSummary

router = APIRouter()

@router.post("/test-morning-email")
async def test_morning_email():
    """Send a test morning email report"""
    try:
        # Initialize services
        claude_service = ClaudeService()
        email_service = EmailService(claude_service=claude_service)
        
        # Mock data for test
        mock_portfolio = PortfolioSummary(
            total_value=100000.0,
            cash_balance=85000.0,
            total_pnl=5000.0,
            open_positions=3,
            win_rate=75.0,
            average_win=1200.0,
            average_loss=-800.0,
            max_drawdown=2.5
        )
        
        mock_opportunities = [
            {
                "symbol": "AAPL",
                "strategy_type": "long_call",
                "confidence": 0.85,
                "target_return": 25.0,
                "time_horizon": 21,
                "rationale": "Strong earnings momentum and technical breakout"
            },
            {
                "symbol": "MSFT",
                "strategy_type": "put_spread",
                "confidence": 0.72,
                "target_return": 18.0,
                "time_horizon": 14,
                "rationale": "Elevated IV providing good credit spread opportunities"
            }
        ]
        
        mock_market_data = {
            "vix": 18.5,
            "spy_price": 458.25,
            "market_sentiment": "Cautiously optimistic",
            "volatility_trend": "Declining from recent highs"
        }
        
        claude_analysis = """
        🎯 TEST MORNING REPORT 🎯
        
        Today's market conditions present several compelling options opportunities:
        
        • AAPL long call - Strong technical setup with earnings catalyst
        • MSFT put spread - High IV rank allows for attractive credit collection
        
        Portfolio is well-positioned with moderate risk exposure and ample cash for new positions.
        
        This is a test email to verify your email configuration is working correctly.
        """
        
        # Send test email
        success = await email_service.send_morning_report(
            opportunities=mock_opportunities,
            portfolio=mock_portfolio,
            market_data=mock_market_data,
            claude_analysis=claude_analysis
        )
        
        if success:
            return {
                "status": "success",
                "message": "Test morning email sent successfully to liam-newell@hotmail.com (from vibe@vibeinvestor.ca)",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")

@router.post("/test-evening-email")
async def test_evening_email():
    """Send a test evening email report"""
    try:
        # Initialize services
        claude_service = ClaudeService()
        email_service = EmailService(claude_service=claude_service)
        
        # Mock portfolio data
        mock_portfolio = PortfolioSummary(
            total_value=102500.0,
            cash_balance=82000.0,
            total_pnl=7500.0,
            open_positions=4,
            win_rate=80.0,
            average_win=1500.0,
            average_loss=-600.0,
            max_drawdown=1.8
        )
        
        # Mock positions (empty for test)
        mock_positions = []
        
        # Mock daily trades
        mock_trades = [
            {
                "time": "10:15 AM",
                "action": "BUY",
                "symbol": "TSLA",
                "strategy": "Long Call",
                "cost": "$2,400",
                "reason": "Claude identified technical breakout pattern"
            },
            {
                "time": "2:30 PM",
                "action": "CLOSE",
                "symbol": "NVDA",
                "strategy": "Put Spread",
                "profit": "+$850",
                "reason": "Reached 75% profit target"
            }
        ]
        
        # Mock performance metrics
        mock_performance = {
            "total_trades": 12,
            "win_rate": 75.0,
            "average_win": 1200.0,
            "average_loss": -450.0,
            "profit_factor": 2.67
        }
        
        # Mock Claude review
        mock_review = {
            "summary": """
            🎯 TEST EVENING REPORT 🎯
            
            Today was a solid trading day with 2 executions:
            
            ✅ NVDA put spread closed for +$850 profit (75% target reached)
            📈 TSLA long call opened based on technical breakout
            
            Portfolio performance continues to track well against targets.
            Risk metrics remain within acceptable parameters.
            
            Tomorrow's focus: Monitor TSLA position and look for additional volatility opportunities.
            
            This is a test email to verify your evening report configuration.
            """,
            "performance_attribution": {"options": "+2.1%", "portfolio": "+0.8%"},
            "tomorrow_strategy": {"focus": "Earnings plays", "risk": "Monitor VIX"}
        }
        
        # Send test email
        success = await email_service.send_evening_report(
            portfolio=mock_portfolio,
            positions=mock_positions,
            daily_trades=mock_trades,
            performance_metrics=mock_performance,
            claude_review=mock_review
        )
        
        if success:
            return {
                "status": "success",
                "message": "Test evening email sent successfully to liam-newell@hotmail.com (from vibe@vibeinvestor.ca)",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")

@router.get("/email-config")
async def check_email_config():
    """Check email configuration status"""
    try:
        from src.core.config import settings
        config = settings.get_email_config()
        
        # Don't expose sensitive information
        safe_config = {
            "enabled": config["enabled"],
            "smtp_server": config["smtp_server"],
            "smtp_port": config["smtp_port"],
            "smtp_user": config["smtp_user"][:3] + "***" if config["smtp_user"] else None,
            "has_password": bool(config["smtp_password"]),
            "alert_email": config["alert_email"],
            "daily_summary": config["daily_summary"],
            "trade_confirmations": config["trade_confirmations"]
        }
        
        return {
            "status": "configured" if config["enabled"] and config["smtp_user"] and config["smtp_password"] else "not_configured",
            "config": safe_config
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config check failed: {str(e)}") 