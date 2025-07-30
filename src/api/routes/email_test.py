"""
Email Test API routes
For testing email configuration
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from src.services.email_service import EmailService
from src.services.claude_service import ClaudeService
from src.models.options import PortfolioSummary, PerformanceHistory

router = APIRouter()

@router.post("/test-morning-email")
async def test_morning_email():
    """Send a test morning email report"""
    try:
        # Initialize services
        claude_service = ClaudeService()
        email_service = EmailService(claude_service=claude_service)
        
        # Mock data for test with enhanced performance tracking
        mock_portfolio = PortfolioSummary(
            total_value=100000.0,
            cash_balance=85000.0,
            total_pnl=5000.0,
            open_positions=3,
            win_rate=75.0,
            average_win=1200.0,
            average_loss=-800.0,
            max_drawdown=2.5,
            performance_history=PerformanceHistory(
                last_7_days_pnl=1850.0,
                last_30_days_pnl=4200.0,
                last_60_days_pnl=5000.0,
                current_streak=3,  # 3 consecutive wins
                consecutive_losses=0,
                days_since_last_win=1,
                recent_win_rate=85.0,  # Recent hot streak
                performance_trend="improving",
                risk_confidence=0.78,
                strategy_performance={
                    "long_call": 2400.0,
                    "put_spread": 1200.0,
                    "iron_condor": 800.0,
                    "credit_spread": 600.0
                }
            )
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
        
        # Mock portfolio data with performance history
        mock_portfolio = PortfolioSummary(
            total_value=102500.0,
            cash_balance=82000.0,
            total_pnl=7500.0,
            open_positions=4,
            win_rate=80.0,
            average_win=1500.0,
            average_loss=-600.0,
            max_drawdown=1.8,
            performance_history=PerformanceHistory(
                last_7_days_pnl=-420.0,   # Recent losses
                last_30_days_pnl=2100.0,  # Still positive overall
                last_60_days_pnl=7500.0,  # Good long-term performance
                current_streak=-2,        # 2 consecutive losses
                consecutive_losses=2,     # 2 losses in a row
                days_since_last_win=3,    # 3 days since last win
                recent_win_rate=65.0,     # Recent performance declining
                performance_trend="declining",
                risk_confidence=0.45,     # Lower confidence due to recent losses
                strategy_performance={
                    "long_call": 3200.0,
                    "put_spread": 2800.0,
                    "iron_condor": 1200.0,
                    "credit_spread": 300.0
                }
            )
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

@router.post("/test-performance-tracking-email")
async def test_performance_tracking_email():
    """Send test emails showcasing enhanced performance tracking features"""
    try:
        # Initialize services
        claude_service = ClaudeService()
        email_service = EmailService(claude_service=claude_service)
        
        # Test 1: Winning streak scenario
        winning_portfolio = PortfolioSummary(
            total_value=118500.0,
            cash_balance=78000.0,
            total_pnl=18500.0,
            open_positions=4,
            win_rate=82.5,
            average_win=1850.0,
            average_loss=-420.0,
            max_drawdown=1.2,
            performance_history=PerformanceHistory(
                last_7_days_pnl=4200.0,    # Strong recent performance
                last_30_days_pnl=15200.0,  # Excellent month
                last_60_days_pnl=18500.0,  # Consistent growth
                current_streak=6,          # 6 consecutive wins 🔥
                consecutive_losses=0,
                days_since_last_win=0,     # Won today
                recent_win_rate=95.0,      # Hot streak
                performance_trend="improving",
                risk_confidence=0.92,      # Very high confidence
                strategy_performance={
                    "long_call": 8200.0,
                    "put_spread": 4800.0,
                    "iron_condor": 3200.0,
                    "credit_spread": 2300.0
                }
            )
        )
        
        mock_opportunities = [
            {
                "symbol": "AAPL",
                "strategy_type": "long_call",
                "confidence": 0.95,
                "target_return": 35.0,
                "time_horizon": 18,
                "rationale": "6-win streak gives high confidence for aggressive play"
            },
            {
                "symbol": "MSFT", 
                "strategy_type": "iron_condor",
                "confidence": 0.88,
                "target_return": 22.0,
                "time_horizon": 21,
                "rationale": "High IV environment perfect for premium collection"
            },
            {
                "symbol": "TSLA",
                "strategy_type": "credit_spread", 
                "confidence": 0.82,
                "target_return": 28.0,
                "time_horizon": 14,
                "rationale": "Earnings volatility creating premium opportunities"
            }
        ]
        
        mock_market_data = {
            "vix": 15.8,
            "spy_price": 472.85,
            "market_sentiment": "Strongly bullish momentum",
            "volatility_trend": "Low volatility favoring aggressive strategies"
        }
        
        claude_analysis = """
        🔥 WINNING STREAK PERFORMANCE ANALYSIS 🔥
        
        Outstanding performance with 6 consecutive wins! Current trajectory analysis:
        
        📈 Performance Metrics:
        • 6-win streak (+$4,200 this week)
        • 95% recent win rate (vs 82.5% overall)
        • Risk confidence at 92% - extremely high
        • All strategies performing well
        
        🎯 Today's Strategy (AGGRESSIVE MODE):
        With current momentum and low VIX, recommending 3 high-confidence positions:
        • AAPL long call - Earnings momentum play
        • MSFT iron condor - Premium collection in stable environment  
        • TSLA credit spread - Volatility arbitrage opportunity
        
        💡 Risk Management: Despite winning streak, maintaining disciplined position sizing
        """
        
        # Send winning streak email
        success1 = await email_service.send_morning_report(
            opportunities=mock_opportunities,
            portfolio=winning_portfolio,
            market_data=mock_market_data,
            claude_analysis=claude_analysis
        )
        
        results = []
        if success1:
            results.append("✅ Winning streak morning email sent successfully")
        else:
            results.append("❌ Failed to send winning streak email")
            
        return {
            "status": "success" if success1 else "partial",
            "message": "Performance tracking email test completed",
            "results": results,
            "demo_features": [
                "🔥 6-win streak display with fire emojis",
                "📈 Progressive performance metrics (7/30/60 days)",
                "⚖️ Adaptive risk level (moderate_aggressive)",
                "🎯 Strategy-specific performance breakdown", 
                "💰 Confidence-based position recommendations",
                "📊 Enhanced visual indicators and color coding"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance tracking email test failed: {str(e)}")

@router.post("/test-comprehensive-email")
async def test_comprehensive_email():
    """Send test emails showing both opportunities and positions with full performance data"""
    try:
        # Initialize services
        claude_service = ClaudeService()
        email_service = EmailService(claude_service=claude_service)
        
        # Morning email with multiple opportunities
        morning_portfolio = PortfolioSummary(
            total_value=105800.0,
            cash_balance=78500.0,
            total_pnl=8200.0,
            open_positions=3,
            win_rate=72.5,
            average_win=1450.0,
            average_loss=-680.0,
            max_drawdown=3.2,
            performance_history=PerformanceHistory(
                last_7_days_pnl=2100.0,
                last_30_days_pnl=7400.0,
                last_60_days_pnl=8200.0,
                current_streak=2,  # 2 consecutive wins
                consecutive_losses=0,
                days_since_last_win=1,
                recent_win_rate=78.0,
                performance_trend="improving",
                risk_confidence=0.72,
                strategy_performance={
                    "long_call": 3200.0,
                    "put_spread": 2800.0,
                    "iron_condor": 1400.0,
                    "credit_spread": 800.0
                }
            )
        )
        
        comprehensive_opportunities = [
            {
                "symbol": "AAPL",
                "strategy_type": "long_call",
                "confidence": 0.85,
                "target_return": 420.0,
                "time_horizon": 18,
                "rationale": "Strong earnings beat expected, technical breakout above resistance"
            },
            {
                "symbol": "MSFT",
                "strategy_type": "iron_condor",
                "confidence": 0.78,
                "target_return": 280.0,
                "time_horizon": 21,
                "rationale": "High IV rank (85th percentile) ideal for premium selling strategies"
            },
            {
                "symbol": "TSLA",
                "strategy_type": "put_spread",
                "confidence": 0.72,
                "target_return": 350.0,
                "time_horizon": 14,
                "rationale": "Earnings volatility creating attractive credit spread opportunities"
            }
        ]
        
        market_data = {
            "vix": 17.2,
            "spy_price": 468.90,
            "market_sentiment": "Cautiously optimistic with earnings momentum",
            "volatility_trend": "Moderate volatility favoring selective strategies"
        }
        
        claude_analysis = """
        📈 PERFORMANCE UPDATE: 2-Win Streak Building Momentum
        
        Current trajectory shows positive momentum with $2,100 gained this week.
        Risk confidence at 72% supports moderate position sizing.
        
        🎯 Today's Strategy: 3 High-Quality Opportunities
        • AAPL long call - Earnings momentum play (85% confidence)
        • MSFT iron condor - Premium collection in elevated IV (78% confidence)  
        • TSLA put spread - Volatility arbitrage before earnings (72% confidence)
        
        📊 Position Scaling: Normal risk level allows for standard sizing across 3 positions.
        Portfolio utilization will increase from current levels but remain within risk parameters.
        """
        
        # Send comprehensive morning email
        success1 = await email_service.send_morning_report(
            opportunities=comprehensive_opportunities,
            portfolio=morning_portfolio,
            market_data=market_data,
            claude_analysis=claude_analysis
        )
        
        # Evening email with actual positions
        from src.models.options import OptionsPosition
        
        evening_portfolio = PortfolioSummary(
            total_value=108200.0,
            cash_balance=75800.0,
            total_pnl=9650.0,
            open_positions=4,
            win_rate=73.8,
            average_win=1520.0,
            average_loss=-620.0,
            max_drawdown=2.8,
            performance_history=PerformanceHistory(
                last_7_days_pnl=3200.0,    # Good week
                last_30_days_pnl=8100.0,   # Strong month
                last_60_days_pnl=9650.0,   # Consistent growth
                current_streak=3,          # 3 wins in a row now
                consecutive_losses=0,
                days_since_last_win=0,     # Won today
                recent_win_rate=82.0,      # Hot streak
                performance_trend="improving",
                risk_confidence=0.78,
                strategy_performance={
                    "long_call": 4200.0,
                    "put_spread": 3100.0,
                    "iron_condor": 1800.0,
                    "credit_spread": 550.0
                }
            )
        )
        
        # Mock position data that shows in the evening email
        mock_positions = [
            {
                "symbol": "AAPL",
                "strategy": "long_call",
                "entry_cost": "$2,400.00",
                "current_value": "$2,820.00",
                "pnl": "$420.00",
                "pnl_pct": "+17.5%",
                "days_held": 5
            },
            {
                "symbol": "MSFT", 
                "strategy": "iron_condor",
                "entry_cost": "$1,800.00",
                "current_value": "$2,080.00", 
                "pnl": "$280.00",
                "pnl_pct": "+15.6%",
                "days_held": 8
            },
            {
                "symbol": "NVDA",
                "strategy": "put_spread",
                "entry_cost": "$1,200.00",
                "current_value": "$1,140.00",
                "pnl": "-$60.00",
                "pnl_pct": "-5.0%",
                "days_held": 3
            },
            {
                "symbol": "SPY",
                "strategy": "credit_spread",
                "entry_cost": "$800.00",
                "current_value": "$920.00",
                "pnl": "$120.00", 
                "pnl_pct": "+15.0%",
                "days_held": 12
            }
        ]
        
        mock_trades = [
            {
                "time": "9:45 AM",
                "action": "BUY",
                "symbol": "TSLA",
                "strategy": "Put Spread",
                "cost": "$1,500",
                "reason": "Claude identified earnings volatility opportunity"
            },
            {
                "time": "2:15 PM", 
                "action": "CLOSE",
                "symbol": "QQQ",
                "strategy": "Iron Condor",
                "profit": "+$380",
                "reason": "Reached 70% profit target early"
            }
        ]
        
        mock_performance = {
            "total_trades": 18,
            "win_rate": 73.8,
            "average_win": 1520.0,
            "average_loss": -620.0,
            "profit_factor": 2.45
        }
        
        mock_review = {
            "summary": """
            🎯 EXCELLENT DAY: 3-Win Streak Extended!
            
            Today's Performance Highlights:
            ✅ AAPL long call: +$420 (+17.5%) - Earnings momentum play worked perfectly
            ✅ QQQ iron condor: +$380 - Closed early at 70% profit target
            ⚠️ NVDA put spread: -$60 (-5.0%) - Minor loss within risk parameters
            
            Portfolio Update:
            • Total value increased to $108,200 (+$2,400 today)
            • 3-win streak building strong momentum  
            • Risk confidence increased to 78%
            • All strategies showing positive attribution
            
            Tomorrow's Strategy: With current momentum, moderate aggressive approach recommended.
            """,
            "performance_attribution": {"options": "+2.2%", "portfolio": "+2.3%"},
            "tomorrow_strategy": {"focus": "Continue momentum plays", "risk": "Moderate aggressive"}
        }
        
        # Send comprehensive evening email
        success2 = await email_service.send_evening_report(
            portfolio=evening_portfolio,
            positions=mock_positions,
            daily_trades=mock_trades,
            performance_metrics=mock_performance,
            claude_review=mock_review
        )
        
        results = []
        if success1:
            results.append("✅ Comprehensive morning email sent (3 opportunities)")
        if success2:
            results.append("✅ Comprehensive evening email sent (4 positions)")
            
        return {
            "status": "success" if (success1 and success2) else "partial",
            "message": "Comprehensive email test completed - check your inbox!",
            "results": results,
            "features_demonstrated": [
                "🎯 Multiple trading opportunities with detailed rationale",
                "📋 Individual position performance with P&L tracking",
                "🔥 Performance streak indicators and trajectory",
                "📈 Strategy-specific performance breakdown",
                "⚖️ Adaptive risk assessment based on performance",
                "🌅 Morning: Action items and opportunities",
                "🌆 Evening: Position review and tomorrow's outlook"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive email test failed: {str(e)}") 