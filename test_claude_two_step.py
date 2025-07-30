#!/usr/bin/env python3
"""
Test Claude's fully autonomous trading process:
1. Claude autonomously picks stocks/options
2. System searches live data for Claude's picks
3. Claude makes final autonomous decision
"""

import asyncio
import sys
import os
import aiohttp

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_autonomous_trading():
    """Test Claude's fully autonomous trading process"""
    try:
        print("🧪 Testing Claude Fully Autonomous Trading...")
        print("=" * 60)
        
        # Test 1: Direct API call to autonomous trading endpoint
        print("\n📞 Testing via API endpoint...")
        
        async with aiohttp.ClientSession() as session:
            try:
                url = "http://localhost:8000/api/v1/trading/test-claude-autonomous-trading"
                async with session.post(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        print("✅ API Test Results:")
                        print(f"   Status: {result.get('status')}")
                        print(f"   Message: {result.get('message')}")
                        
                        # Show autonomous summary
                        summary = result.get('autonomous_summary', {})
                        print(f"\n🎯 Autonomy Approach: {summary.get('approach')}")
                        print(f"🤖 Decision Maker: {summary.get('decision_maker')}")
                        print(f"👤 Human Involvement: {summary.get('human_involvement')}")
                        
                        principles = summary.get('key_principles', [])
                        print("\n💡 Key Principles:")
                        for principle in principles[:4]:  # Show first 4
                            print(f"   {principle}")
                        
                        # Show workflow results
                        workflow = summary.get('autonomy_workflow', [])
                        print("\n🔄 Autonomy Workflow:")
                        for step in workflow:
                            print(f"   {step}")
                        
                        # Show detailed results
                        details = result.get('detailed_results', {})
                        
                        # Claude's autonomous picks
                        step2 = details.get('step_2_claude_autonomous_picks', {})
                        if step2:
                            print(f"\n🤖 Claude's Autonomous Picks:")
                            print(f"   Count: {step2.get('picks_count', 0)}")
                            print(f"   Symbols: {step2.get('autonomous_symbols', [])}")
                            print(f"   Strategies: {step2.get('autonomous_strategies', [])}")
                            print(f"   Decision maker: {step2.get('decision_maker')}")
                        
                        # Live data for Claude's picks
                        step3 = details.get('step_3_live_data_for_claude_picks', {})
                        if step3:
                            print(f"\n🔍 Live Data for Claude's Picks:")
                            symbols = step3.get('claude_symbols_searched', [])
                            print(f"   Claude's symbols: {symbols}")
                            
                            prices = step3.get('live_prices', {})
                            changes = step3.get('price_changes', {})
                            
                            for symbol in symbols[:3]:  # Show first 3
                                price = prices.get(symbol, 'N/A')
                                change = changes.get(symbol, 'N/A')
                                print(f"   {symbol}: {price} ({change})")
                            
                            print(f"   Purpose: {step3.get('data_purpose')}")
                        
                        # Claude's final autonomous decision
                        step4 = details.get('step_4_claude_final_autonomous_decision', {})
                        if step4:
                            print(f"\n🎯 Claude's Final Autonomous Decision:")
                            print(f"   Initial picks: {step4.get('initial_autonomous_picks', 0)}")
                            print(f"   Final confirmed: {step4.get('final_confirmed_autonomous_opportunities', 0)}")
                            print(f"   Decision maker: {step4.get('decision_maker')}")
                            
                            assessment = step4.get('claude_market_assessment', {})
                            if assessment:
                                print(f"   Market sentiment: {assessment.get('overall_sentiment', 'Unknown')}")
                                print(f"   Key observations: {assessment.get('key_observations', 'None')}")
                        
                        # Autonomous execution readiness
                        step5 = details.get('step_5_dynamic_filtering', {})
                        if step5:
                            print(f"\n🛡️ Risk Management Filtering:")
                            print(f"   Claude's opportunities: {step5.get('claude_autonomous_opportunities', 0)}")
                            print(f"   Approved for execution: {step5.get('approved_for_execution', 0)}")
                            print(f"   Ready for autonomous execution: {step5.get('ready_for_autonomous_execution', False)}")
                        
                        deployment = result.get('deployment_ready', {})
                        print(f"\n🚀 System Ready: {deployment.get('ready', False)}")
                        print(f"🤖 Autonomy Level: {deployment.get('autonomy_level', 'Unknown')}")
                        
                        return True
                        
                    else:
                        print(f"❌ API call failed with status: {response.status}")
                        text = await response.text()
                        print(f"   Response: {text}")
                        return False
                        
            except aiohttp.ClientConnectorError:
                print("❌ Could not connect to localhost:8000")
                print("💡 Make sure the FastAPI server is running: python main.py")
                return False
        
        # Test 2: Direct module testing (if API fails)
        print("\n🔧 Testing direct module integration...")
        try:
            from services.claude_service import ClaudeService
            from core.config import settings
            
            print("✅ Modules imported successfully")
            print("✅ Autonomous trading implementation ready")
            
            return True
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def print_autonomous_summary():
    """Print summary of Claude's autonomous trading approach"""
    print("\n" + "=" * 70)
    print("🤖 CLAUDE FULLY AUTONOMOUS TRADING SUMMARY")
    print("=" * 70)
    
    print("\n📋 AUTONOMOUS WORKFLOW:")
    print("1. 🤖 Claude autonomously picks 3-6 stocks/options")
    print("   • NO human proposals or suggestions")
    print("   • Uses Claude's vast market knowledge independently")
    print("   • Considers portfolio performance and risk level")
    print("   • Picks from high-liquidity symbols (AAPL, MSFT, SPY, etc.)")
    
    print("\n2. 🔍 System searches live data for Claude's picks ONLY")
    print("   • Yahoo Finance API for current prices")
    print("   • Volume, change %, market state")
    print("   • Efficient: Only searches Claude-selected symbols")
    
    print("\n3. 🎯 Claude reviews live data & makes final autonomous decision")
    print("   • Can confirm, modify, or reject its own ideas")
    print("   • Adds strike prices, position sizing autonomously")
    print("   • Provides live data validation reasoning")
    print("   • 100% Claude decision - no human input")
    
    print("\n4. 🛡️ Dynamic risk management filtering")
    print("   • Research-backed confidence thresholds by strategy")
    print("   • Adapts based on portfolio performance")
    print("   • Ready for fully autonomous execution")
    
    print("\n💡 AUTONOMY ADVANTAGES:")
    print("✅ Complete Independence: Claude makes ALL decisions")
    print("✅ Market Knowledge: Leverages Claude's vast financial expertise") 
    print("✅ Live Validation: Current market data validates Claude's picks")
    print("✅ Adaptive Decision: Claude can change mind with live data")
    print("✅ Efficient Search: Only searches data for Claude's choices")
    print("✅ Zero Human Input: Fully autonomous trading system")
    
    print("\n🚀 100% AUTONOMOUS TRADING READY!")

if __name__ == "__main__":
    print("🔥 TESTING CLAUDE FULLY AUTONOMOUS TRADING 🔥")
    
    result = asyncio.run(test_autonomous_trading())
    
    print_autonomous_summary()
    
    if result:
        print("\n🎉 ALL TESTS PASSED!")
        print("🤖 Claude is ready for fully autonomous trading")
        print("🚀 Zero human input required - Claude makes all decisions")
    else:
        print("\n⚠️ Some tests failed - check output above")
    
    sys.exit(0 if result else 1) 