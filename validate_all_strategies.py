#!/usr/bin/env python3
"""
Validate All Strategies - Test and Display All Strategy Types Working Correctly
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from src.services.options_service import OptionsService
from src.services.market_data_service import MarketDataService
from src.models.options import StrategyType, OptionsPosition, OptionContract, PortfolioSummary, PerformanceHistory

# Setup logging  
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def validate_all_strategies():
    """Validate all strategy types work correctly and display results"""
    
    print("🎯 VALIDATING ALL STRATEGY TYPES")
    print("=" * 60)
    
    # Initialize services
    options_service = OptionsService()
    market_service = MarketDataService()
    
    await options_service.initialize()
    
    print(f"📊 System Status:")
    print(f"   💰 Cash Balance: ${options_service.cash_balance:,.2f}")
    print(f"   📝 Paper Trading: {options_service.paper_trading_enabled}")
    print(f"   🕒 Market Hours: {market_service.is_market_hours()}")
    print(f"   📈 Current Positions: {len(options_service.positions)}")
    print()
    
    # Define all strategy test cases
    strategy_tests = [
        {
            "strategy": StrategyType.LONG_CALL,
            "symbol": "SPY",
            "description": "Bullish strategy - buy call option",
            "typical_cost": 500,
            "contracts_expected": 1,
            "example": "Buy SPY $550 Call expiring in 3 weeks"
        },
        {
            "strategy": StrategyType.LONG_PUT, 
            "symbol": "QQQ",
            "description": "Bearish strategy - buy put option",
            "typical_cost": 400,
            "contracts_expected": 1,
            "example": "Buy QQQ $450 Put expiring in 3 weeks"
        },
        {
            "strategy": StrategyType.CALL_SPREAD,
            "symbol": "AAPL", 
            "description": "Limited upside bullish spread",
            "typical_cost": 300,
            "contracts_expected": 2,
            "example": "Buy AAPL $180 Call, Sell AAPL $190 Call"
        },
        {
            "strategy": StrategyType.PUT_SPREAD,
            "symbol": "MSFT",
            "description": "Limited downside bearish spread", 
            "typical_cost": 250,
            "contracts_expected": 2,
            "example": "Buy MSFT $420 Put, Sell MSFT $410 Put"
        },
        {
            "strategy": StrategyType.IRON_CONDOR,
            "symbol": "NVDA",
            "description": "Range-bound neutral strategy",
            "typical_cost": 200,
            "contracts_expected": 4,
            "example": "Sell NVDA $140/145 Call spread + Sell $130/125 Put spread"
        }
    ]
    
    # Portfolio for testing
    portfolio = PortfolioSummary(
        total_value=options_service.portfolio_value,
        cash_balance=options_service.cash_balance,
        total_pnl=0.0,
        open_positions=len(options_service.positions),
        performance_history=PerformanceHistory()
    )
    
    results = []
    
    print("🧪 TESTING EACH STRATEGY TYPE")
    print("=" * 60)
    
    for i, test in enumerate(strategy_tests, 1):
        strategy = test["strategy"]
        symbol = test["symbol"]
        
        print(f"\n{i}. {strategy.value.upper().replace('_', ' ')}")
        print(f"   📍 Symbol: {symbol}")
        print(f"   📝 Description: {test['description']}")
        print(f"   💡 Example: {test['example']}")
        print(f"   💰 Typical Cost: ${test['typical_cost']}")
        
        try:
            # Create test opportunity
            opportunity = {
                "symbol": symbol,
                "strategy_type": strategy.value,
                "confidence": 0.75,
                "target_return": test['typical_cost'] * 1.5,  # 50% return target
                "max_risk": test['typical_cost'],
                "time_horizon": 21,  # 3 weeks
                "profit_target": test['typical_cost'] * 1.4,
                "entry_cost": test['typical_cost']
            }
            
            # Test position creation
            print(f"   🔧 Creating position from opportunity...")
            position = await options_service.create_position_from_opportunity(opportunity, portfolio)
            
            if position:
                print(f"   ✅ Position Created Successfully!")
                print(f"      🏷️ ID: {str(position.id)[:8]}...")
                print(f"      📊 Strategy: {position.strategy_type.value}")
                print(f"      📈 Contracts: {len(position.contracts)} (expected: {test['contracts_expected']})")
                print(f"      💰 Entry Cost: ${position.entry_cost:.2f}")
                print(f"      🎯 Profit Target: ${position.profit_target:.2f}")
                print(f"      🛡️ Max Loss: ${position.max_loss:.2f}")
                print(f"      🕒 Entry Date: {position.entry_date.strftime('%Y-%m-%d %H:%M')}")
                
                # Validate contract structure
                contracts_valid = True
                if len(position.contracts) != test['contracts_expected']:
                    contracts_valid = False
                    print(f"      ⚠️ Contract count mismatch: got {len(position.contracts)}, expected {test['contracts_expected']}")
                
                # Test position execution
                print(f"   🚀 Testing position execution...")
                execution_success = await options_service.create_position(position)
                
                if execution_success:
                    print(f"   ✅ EXECUTION SUCCESSFUL!")
                    print(f"      💳 New Cash Balance: ${options_service.cash_balance:,.2f}")
                    results.append({
                        "strategy": strategy.value,
                        "symbol": symbol,
                        "status": "SUCCESS",
                        "contracts": len(position.contracts),
                        "cost": position.entry_cost,
                        "executed": True
                    })
                else:
                    print(f"   ❌ EXECUTION FAILED")
                    results.append({
                        "strategy": strategy.value,
                        "symbol": symbol, 
                        "status": "EXECUTION_FAILED",
                        "contracts": len(position.contracts),
                        "cost": position.entry_cost,
                        "executed": False
                    })
            else:
                print(f"   ❌ POSITION CREATION FAILED")
                results.append({
                    "strategy": strategy.value,
                    "symbol": symbol,
                    "status": "CREATION_FAILED",
                    "contracts": 0,
                    "cost": 0,
                    "executed": False
                })
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                "strategy": strategy.value,
                "symbol": symbol,
                "status": "ERROR",
                "error": str(e),
                "contracts": 0,
                "cost": 0,
                "executed": False
            })
    
    # Display comprehensive results
    print(f"\n📊 VALIDATION RESULTS SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    total = len(results)
    
    print(f"✅ Successful Strategies: {successful}/{total}")
    print(f"💰 Total Capital Used: ${sum(r.get('cost', 0) for r in results):,.2f}")
    print(f"💳 Remaining Cash: ${options_service.cash_balance:,.2f}")
    print(f"📝 Active Positions: {len(options_service.positions)}")
    
    print(f"\n📋 DETAILED RESULTS:")
    print("-" * 60)
    
    for result in results:
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} {result['strategy'].upper().replace('_', ' ')}")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Status: {result['status']}")
        print(f"   Contracts: {result['contracts']}")
        print(f"   Cost: ${result['cost']:.2f}")
        if 'error' in result:
            print(f"   Error: {result['error']}")
        print()
    
    # Display current positions
    active_positions = await options_service.get_active_positions()
    print(f"🔍 ACTIVE POSITIONS ({len(active_positions)}):")
    print("-" * 40)
    
    if active_positions:
        for pos in active_positions:
            print(f"• {pos.symbol} {pos.strategy_type.value}")
            print(f"  💰 Cost: ${pos.entry_cost:.0f} | P&L: ${pos.unrealized_pnl:+.0f}")
            print(f"  📊 Contracts: {len(pos.contracts)} | Delta: {pos.portfolio_delta:.2f}")
    else:
        print("  No active positions")
    
    print(f"\n🎯 STRATEGY VALIDATION COMPLETE!")
    
    if successful == total:
        print(f"🎉 ALL STRATEGIES WORKING PERFECTLY!")
    else:
        print(f"⚠️ {total - successful} strategies need attention")
    
    await market_service.close()
    return results

if __name__ == "__main__":
    asyncio.run(validate_all_strategies())