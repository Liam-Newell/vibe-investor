#!/usr/bin/env python3
"""
Test Strategy Execution - Validate All Strategy Types Work Correctly
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from src.services.options_service import OptionsService
from src.services.market_data_service import MarketDataService
from src.models.options import StrategyType, OptionsPosition, OptionContract, PortfolioSummary, PerformanceHistory
from src.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_all_strategies():
    """Test all strategy types to ensure they work correctly"""
    
    print("🧪 TESTING ALL STRATEGY TYPES")
    print("=" * 50)
    
    # Initialize services
    options_service = OptionsService()
    market_service = MarketDataService()
    
    await options_service.initialize()
    
    print(f"📊 Initial State:")
    print(f"   Cash Balance: ${options_service.cash_balance:,.2f}")
    print(f"   Positions: {len(options_service.positions)}")
    print(f"   Market Hours: {market_service.is_market_hours()}")
    print(f"   Paper Trading: {options_service.paper_trading_enabled}")
    print(f"   Auto Execute: {settings.AUTO_EXECUTE_TRADES}")
    print()
    
    # Test data for each strategy
    test_opportunities = [
        {
            "symbol": "SPY",
            "strategy_type": "long_call",
            "confidence": 0.75,
            "entry_cost": 500.0,
            "profit_target": 750.0,
            "max_loss": 250.0,
            "time_horizon": "2 weeks"
        },
        {
            "symbol": "QQQ", 
            "strategy_type": "long_put",
            "confidence": 0.70,
            "entry_cost": 400.0,
            "profit_target": 600.0,
            "max_loss": 200.0,
            "time_horizon": "3 weeks"
        },
        {
            "symbol": "AAPL",
            "strategy_type": "call_spread", 
            "confidence": 0.65,
            "entry_cost": 300.0,
            "profit_target": 450.0,
            "max_loss": 150.0,
            "time_horizon": "1 month"
        },
        {
            "symbol": "MSFT",
            "strategy_type": "iron_condor",
            "confidence": 0.68,
            "entry_cost": 200.0,
            "profit_target": 300.0,
            "max_loss": 100.0,
            "time_horizon": "3 weeks"
        }
    ]
    
    # Create a portfolio summary for testing
    portfolio = PortfolioSummary(
        total_value=options_service.portfolio_value,
        cash_balance=options_service.cash_balance,
        total_pnl=0.0,
        open_positions=len(options_service.positions),
        performance_history=PerformanceHistory()
    )
    
    executed_positions = []
    
    print("🎯 TESTING STRATEGY EXECUTION")
    print("-" * 30)
    
    for i, opportunity in enumerate(test_opportunities, 1):
        strategy_type = opportunity["strategy_type"]
        symbol = opportunity["symbol"]
        
        print(f"\n{i}. Testing {strategy_type.upper()} on {symbol}")
        print(f"   Target Cost: ${opportunity['entry_cost']:.0f}")
        print(f"   Confidence: {opportunity['confidence']:.2f}")
        
        try:
            # Create position from opportunity
            position = await options_service.create_position_from_opportunity(opportunity, portfolio)
            
            if position:
                print(f"   ✅ Position created: {len(position.contracts)} contracts")
                print(f"   📋 Strategy: {position.strategy_type.value}")
                print(f"   💰 Entry Cost: ${position.entry_cost:.2f}")
                print(f"   🎯 Profit Target: ${position.profit_target:.2f}")
                print(f"   🛡️ Max Loss: ${position.max_loss:.2f}")
                
                # Try to execute the position
                success = await options_service.create_position(position)
                
                if success:
                    executed_positions.append(position)
                    print(f"   🚀 EXECUTED SUCCESSFULLY!")
                    print(f"   💳 New Cash Balance: ${options_service.cash_balance:.2f}")
                else:
                    print(f"   ❌ EXECUTION FAILED")
            else:
                print(f"   ❌ POSITION CREATION FAILED")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n📊 EXECUTION SUMMARY")
    print("=" * 30)
    print(f"✅ Successfully executed: {len(executed_positions)} positions")
    print(f"💰 Cash used: ${options_service.portfolio_value - options_service.cash_balance:.2f}")
    print(f"💳 Remaining cash: ${options_service.cash_balance:.2f}")
    print(f"📝 Total positions: {len(options_service.positions)}")
    
    if executed_positions:
        print(f"\n📋 EXECUTED POSITIONS:")
        for pos in executed_positions:
            print(f"   • {pos.symbol} {pos.strategy_type.value}: ${pos.entry_cost:.0f}")
    
    # Display current positions
    active_positions = await options_service.get_active_positions()
    print(f"\n🔍 ACTIVE POSITIONS IN MEMORY: {len(active_positions)}")
    for pos in active_positions:
        print(f"   • {pos.symbol} {pos.strategy_type.value} - ${pos.entry_cost:.0f} (P&L: ${pos.unrealized_pnl:+.0f})")
    
    await market_service.close()
    
    return executed_positions

if __name__ == "__main__":
    asyncio.run(test_all_strategies())