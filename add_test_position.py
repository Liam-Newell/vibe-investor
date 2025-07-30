#!/usr/bin/env python3
"""
Add Test Position Utility
Quick way to add sample positions for testing the dashboard
"""

import json
from datetime import datetime, timedelta
from positions_db import db, Position

def add_test_position(symbol: str, strategy: str, entry_cost: float):
    """Add a test position to the database"""
    
    # Create expiry date 30 days from now
    expiry_date = (datetime.now() + timedelta(days=30)).isoformat()
    
    # Create contract data
    contract_data = {
        "strike": 230 if symbol == "AAPL" else 415 if symbol == "MSFT" else 450,
        "expiry": expiry_date,
        "quantity": 1,
        "option_type": "call" if "Call" in strategy else "put"
    }
    
    position = Position(
        id=f"test_{symbol.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        symbol=symbol,
        strategy=strategy,
        entry_cost=entry_cost,
        entry_date=datetime.now().isoformat(),
        contracts_data=json.dumps(contract_data),
        profit_target=entry_cost * 1.25,  # 25% profit target
        max_loss=entry_cost * 0.75,       # 25% max loss
        current_value=entry_cost,         # Start at entry cost
        unrealized_pnl=0.0               # Start at break-even
    )
    
    success = db.add_position(position)
    
    if success:
        print(f"✅ Added test position: {symbol} {strategy} (${entry_cost:,.0f})")
        return True
    else:
        print(f"❌ Failed to add position: {symbol} {strategy}")
        return False

def main():
    """Main function to add test positions"""
    print("🧪 Adding Test Positions to Database...")
    print("=" * 50)
    
    # Get current portfolio state
    portfolio = db.get_portfolio_summary()
    positions = db.get_all_positions()
    
    print(f"📊 Current Portfolio: ${portfolio['total_value']:,.0f}")
    print(f"📋 Current Positions: {len(positions)}")
    
    if len(positions) > 0:
        print("\n💡 Existing positions found:")
        for pos in positions:
            print(f"   • {pos.symbol} {pos.strategy} (${pos.entry_cost:,.0f})")
        
        response = input("\n❓ Add more test positions? (y/n): ").lower()
        if response != 'y':
            print("👋 Exiting without changes")
            return
    
    # Add test positions
    test_positions = [
        ("AAPL", "Long Call", 2500),
        ("MSFT", "Iron Condor", 1800),
        ("SPY", "Put Spread", 3200)
    ]
    
    print(f"\n📝 Adding {len(test_positions)} test positions...")
    
    added_count = 0
    for symbol, strategy, cost in test_positions:
        if add_test_position(symbol, strategy, cost):
            added_count += 1
    
    print(f"\n🎉 Successfully added {added_count}/{len(test_positions)} test positions!")
    
    # Show updated portfolio
    portfolio = db.get_portfolio_summary()
    positions = db.get_all_positions()
    
    print("\n📊 Updated Portfolio:")
    print(f"   Total Value: ${portfolio['total_value']:,.0f}")
    print(f"   Open Positions: {portfolio['open_positions']}")
    print(f"   Held Symbols: {db.get_held_symbols()}")
    
    print("\n🌐 Dashboard: http://localhost:8000/")
    print("🔄 Refresh the dashboard to see your test positions!")

if __name__ == "__main__":
    main() 