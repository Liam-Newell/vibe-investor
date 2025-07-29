"""
Trading API routes
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from src.services.claude_service import ClaudeService
from src.models.options import PortfolioSummary, PerformanceHistory

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

@router.post("/test-morning-strategy")
async def test_morning_strategy():
    """
    TEST ENDPOINT: Get Claude AI's actual stock recommendations for tomorrow
    This demonstrates how the system generates real trading decisions
    """
    try:
        # Initialize Claude service
        claude_service = ClaudeService()
        
        # Mock current portfolio (paper trading starting point)
        mock_portfolio = PortfolioSummary(
            total_value=100000.0,
            cash_balance=85000.0,
            total_pnl=0.0,
            open_positions=0,
            win_rate=0.0,
            average_win=0.0,
            average_loss=0.0,
            max_drawdown=0.0,
            total_delta=0.0,
            total_vega=0.0,
            performance_history=PerformanceHistory(
                last_7_days_pnl=0.0,
                last_30_days_pnl=0.0,
                last_60_days_pnl=0.0,
                current_streak=0,
                consecutive_losses=0,
                days_since_last_win=0,
                recent_win_rate=0.0,
                performance_trend="neutral",
                risk_confidence=0.5,
                strategy_performance={}
            )
        )
        
        # Mock current market data
        mock_market_data = {
            "vix": 18.5,
            "spy_price": 458.25,
            "spy_change_pct": 0.8,
            "market_sentiment": "Cautiously optimistic", 
            "volatility_trend": "Declining from recent highs",
            "economic_calendar": [
                {"event": "Fed Meeting Minutes", "date": "2024-02-01", "importance": "high"},
                {"event": "Jobs Report", "date": "2024-02-02", "importance": "high"}
            ]
        }
        
        # Mock earnings calendar (next 2 weeks)
        tomorrow = date.today() + timedelta(days=1)
        mock_earnings = [
            {
                "symbol": "AAPL", 
                "date": (tomorrow + timedelta(days=7)).isoformat(),
                "estimate": 2.05,
                "importance": "high"
            },
            {
                "symbol": "MSFT",
                "date": (tomorrow + timedelta(days=10)).isoformat(), 
                "estimate": 2.78,
                "importance": "high"
            },
            {
                "symbol": "TSLA",
                "date": (tomorrow + timedelta(days=5)).isoformat(),
                "estimate": 0.85,
                "importance": "medium"
            }
        ]
        
        # Get Claude's actual recommendations
        strategy_response = await claude_service.morning_strategy_session(
            portfolio=mock_portfolio,
            market_data=mock_market_data,
            earnings_calendar=mock_earnings,
            current_positions=[]
        )
        
        # Format response to show what the trading system would do
        trading_plan = {
            "timestamp": datetime.now().isoformat(),
            "market_analysis": mock_market_data,
            "portfolio_status": {
                "cash_available": mock_portfolio.cash_balance,
                "current_positions": mock_portfolio.open_positions,
                "portfolio_delta": mock_portfolio.total_delta,
                "portfolio_vega": mock_portfolio.total_vega
            },
            "claude_market_assessment": {
                "overall_sentiment": strategy_response.market_assessment.overall_sentiment,
                "volatility_environment": strategy_response.market_assessment.volatility_environment,
                "opportunity_quality": strategy_response.market_assessment.opportunity_quality,
                "recommended_exposure": strategy_response.market_assessment.recommended_exposure
            },
            "claude_cash_strategy": {
                "action": strategy_response.cash_strategy.action,
                "reasoning": strategy_response.cash_strategy.reasoning,
                "target_cash_percentage": strategy_response.cash_strategy.target_cash_percentage,
                "urgency": strategy_response.cash_strategy.urgency
            },
            "claude_recommendations": [
                {
                    "symbol": opp.symbol,
                    "strategy": opp.strategy_type,
                    "confidence": opp.confidence,
                    "target_return": opp.target_return,
                    "max_risk": opp.max_risk,
                    "time_horizon_days": opp.time_horizon,
                    "rationale": opp.rationale,
                    "risk_assessment": opp.risk_assessment,
                    "contracts": opp.contracts,
                    "priority": opp.priority
                } for opp in strategy_response.opportunities
            ],
            "position_scaling": {
                "max_allowed_positions": 6,
                "current_positions": mock_portfolio.open_positions,
                "available_slots": 6 - mock_portfolio.open_positions,
                "recommended_new_positions": len(strategy_response.opportunities),
                "scaling_rationale": f"Claude recommends {len(strategy_response.opportunities)} positions based on {strategy_response.market_assessment.opportunity_quality} market opportunities"
            },
            "next_actions": [
                f"💰 Cash Strategy: {strategy_response.cash_strategy.action.replace('_', ' ').title()}",
                f"📊 Paper trade {len(strategy_response.opportunities)} positions" if strategy_response.opportunities else "🔍 Hold cash - no trades identified today",
                "⏰ Monitor positions throughout day",
                "📧 Send evening report with results",
                "🌅 Generate tomorrow's morning strategy"
            ],
            "paper_trading_note": "🔒 SAFE: All trades will be simulated with paper money until 60+ days of successful testing"
        }
        
        return {
            "status": "success",
            "message": f"✅ Claude AI assessed market as '{strategy_response.market_assessment.overall_sentiment}' and recommends '{strategy_response.cash_strategy.action}' with {len(strategy_response.opportunities)} opportunities",
            "trading_plan": trading_plan,
            "system_status": "ready_for_automated_paper_trading"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Morning strategy test failed: {str(e)}")

@router.post("/simulate-paper-trade")
async def simulate_paper_trade():
    """
    TEST ENDPOINT: Simulate how the system executes Claude's recommendations
    """
    return {
        "status": "simulated",
        "message": "Paper trade simulation completed",
        "execution": {
            "trades_executed": 2,
            "total_risk": 1200.0,
            "expected_return": "15-25%",
            "time_horizon": "2-3 weeks",
            "portfolio_impact": {
                "new_delta": 0.15,
                "new_vega": 200.0,
                "cash_used": 1200.0,
                "cash_remaining": 83800.0
            }
        },
        "monitoring": {
            "position_tracking": "Active",
            "risk_alerts": "Enabled", 
            "claude_position_reviews": "Every 2 days",
            "automatic_adjustments": "Enabled"
        }
    } 

@router.post("/test-winning-streak-strategy")
async def test_winning_streak_strategy():
    """
    TEST ENDPOINT: Show how Claude becomes more aggressive after a winning streak
    """
    try:
        claude_service = ClaudeService()
        
        # Mock portfolio with winning streak
        mock_portfolio = PortfolioSummary(
            total_value=115000.0,  # Up 15%
            cash_balance=80000.0,
            total_pnl=15000.0,     # Profitable
            open_positions=2,
            win_rate=75.0,         # Good win rate
            average_win=1800.0,
            average_loss=-600.0,
            max_drawdown=2.0,      # Low drawdown
            total_delta=0.15,
            total_vega=200.0,
            performance_history=PerformanceHistory(
                last_7_days_pnl=3200.0,    # Recent profits
                last_30_days_pnl=12000.0,  # Strong month
                last_60_days_pnl=15000.0,  # Consistent gains
                current_streak=5,          # 5 wins in a row
                consecutive_losses=0,      # No recent losses
                days_since_last_win=1,     # Recent win
                recent_win_rate=80.0,      # Hot streak
                performance_trend="improving",
                risk_confidence=0.85,      # High confidence
                strategy_performance={
                    "credit_spread": 1200.0,
                    "iron_condor": 800.0,
                    "long_call": 2000.0
                }
            )
        )
        
        mock_market_data = {
            "vix": 16.2,  # Lower volatility
            "spy_price": 465.80,
            "spy_change_pct": 1.2,
            "market_sentiment": "Bullish optimism",
            "volatility_trend": "Declining - favorable for option selling"
        }
        
        # Test during winning streak
        strategy_response = await claude_service.morning_strategy_session(
            portfolio=mock_portfolio,
            market_data=mock_market_data,
            earnings_calendar=[],
            current_positions=[]
        )
        
        return {
            "status": "success",
            "scenario": "WINNING STREAK",
            "message": f"✅ After 5-win streak (+$15K profit), Claude recommends '{strategy_response.cash_strategy.action}' with {len(strategy_response.opportunities)} opportunities",
            "performance_context": {
                "current_streak": "5 consecutive wins",
                "recent_pnl": "+$3,200 (7 days), +$12,000 (30 days)",
                "risk_level": mock_portfolio.get_adaptive_risk_level(),
                "confidence": f"{mock_portfolio.risk_adjusted_confidence:.1%}",
                "position_size_multiplier": f"{mock_portfolio.suggested_position_size_multiplier:.2f}x"
            },
            "claude_response": {
                "market_sentiment": strategy_response.market_assessment.overall_sentiment,
                "recommended_exposure": strategy_response.market_assessment.recommended_exposure,
                "cash_strategy": strategy_response.cash_strategy.action,
                "opportunities_count": len(strategy_response.opportunities),
                "reasoning": strategy_response.cash_strategy.reasoning
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Winning streak test failed: {str(e)}")

@router.post("/test-losing-streak-strategy") 
async def test_losing_streak_strategy():
    """
    TEST ENDPOINT: Show how Claude becomes more conservative after losses
    """
    try:
        claude_service = ClaudeService()
        
        # Mock portfolio with losing streak
        mock_portfolio = PortfolioSummary(
            total_value=92000.0,   # Down 8%
            cash_balance=88000.0,
            total_pnl=-8000.0,     # Losses
            open_positions=1,      # Reduced positions
            win_rate=40.0,         # Poor win rate
            average_win=800.0,
            average_loss=-1200.0,  # Larger losses
            max_drawdown=12.0,     # High drawdown
            total_delta=0.05,      # Low exposure
            total_vega=50.0,
            performance_history=PerformanceHistory(
                last_7_days_pnl=-2400.0,   # Recent losses
                last_30_days_pnl=-6500.0,  # Poor month
                last_60_days_pnl=-8000.0,  # Consistent losses
                current_streak=-4,         # 4 losses in a row
                consecutive_losses=4,      # 4 consecutive losses
                days_since_last_win=12,    # No recent wins
                recent_win_rate=25.0,      # Cold streak
                performance_trend="declining",
                risk_confidence=0.25,      # Low confidence
                strategy_performance={
                    "long_call": -3200.0,
                    "put_spread": -1800.0,
                    "iron_condor": -1000.0
                }
            )
        )
        
        mock_market_data = {
            "vix": 22.8,  # Higher volatility
            "spy_price": 442.15,
            "spy_change_pct": -0.8,
            "market_sentiment": "Cautious amid uncertainty",
            "volatility_trend": "Elevated - challenging for option strategies"
        }
        
        # Test during losing streak
        strategy_response = await claude_service.morning_strategy_session(
            portfolio=mock_portfolio,
            market_data=mock_market_data,
            earnings_calendar=[],
            current_positions=[]
        )
        
        return {
            "status": "success", 
            "scenario": "LOSING STREAK",
            "message": f"⚠️ After 4 consecutive losses (-$8K), Claude recommends '{strategy_response.cash_strategy.action}' with {len(strategy_response.opportunities)} opportunities",
            "performance_context": {
                "current_streak": "4 consecutive losses",
                "recent_pnl": "-$2,400 (7 days), -$6,500 (30 days)",
                "risk_level": mock_portfolio.get_adaptive_risk_level(),
                "confidence": f"{mock_portfolio.risk_adjusted_confidence:.1%}",
                "position_size_multiplier": f"{mock_portfolio.suggested_position_size_multiplier:.2f}x"
            },
            "claude_response": {
                "market_sentiment": strategy_response.market_assessment.overall_sentiment,
                "recommended_exposure": strategy_response.market_assessment.recommended_exposure,
                "cash_strategy": strategy_response.cash_strategy.action,
                "opportunities_count": len(strategy_response.opportunities),
                "reasoning": strategy_response.cash_strategy.reasoning
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Losing streak test failed: {str(e)}") 