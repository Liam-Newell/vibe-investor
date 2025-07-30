"""
Web Search Utility for Live Stock Data
Searches for current stock prices and market information
"""

import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

async def search_stock_data(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Search for live stock data using web search
    Returns current price, change, volume, and other relevant data
    """
    try:
        # Try multiple data sources for reliability
        sources = [
            _search_yahoo_finance,
            _search_marketwatch,
            _search_google_finance
        ]
        
        for search_func in sources:
            try:
                result = await search_func(symbol)
                if result and result.get('price'):
                    logger.info(f"✅ Found stock data for {symbol} via {search_func.__name__}")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ {search_func.__name__} failed for {symbol}: {e}")
                continue
        
        logger.warning(f"❌ All search methods failed for {symbol}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Stock data search failed for {symbol}: {e}")
        return None

async def _search_yahoo_finance(symbol: str) -> Optional[Dict[str, Any]]:
    """Search Yahoo Finance for stock data"""
    try:
        # Use Yahoo Finance API (unofficial but reliable)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'chart' in data and data['chart']['result']:
                        result = data['chart']['result'][0]
                        meta = result.get('meta', {})
                        
                        current_price = meta.get('regularMarketPrice')
                        previous_close = meta.get('previousClose', current_price)
                        
                        if current_price and previous_close:
                            change_pct = ((current_price - previous_close) / previous_close) * 100
                            
                            return {
                                'symbol': symbol,
                                'price': current_price,
                                'change_pct': change_pct,
                                'volume': meta.get('regularMarketVolume', 0),
                                'previous_close': previous_close,
                                'currency': meta.get('currency', 'USD'),
                                'market_state': meta.get('marketState', 'UNKNOWN'),
                                'timestamp': datetime.now().isoformat(),
                                'source': 'Yahoo Finance'
                            }
        
        return None
        
    except Exception as e:
        logger.warning(f"Yahoo Finance search failed: {e}")
        return None

async def _search_marketwatch(symbol: str) -> Optional[Dict[str, Any]]:
    """Search MarketWatch for stock data (simplified scraping)"""
    try:
        # This would require proper web scraping
        # For now, return None to fall back to other methods
        return None
        
    except Exception as e:
        logger.warning(f"MarketWatch search failed: {e}")
        return None

async def _search_google_finance(symbol: str) -> Optional[Dict[str, Any]]:
    """Search Google Finance for stock data"""
    try:
        # Google Finance doesn't have a public API
        # Would need web scraping which is complex
        return None
        
    except Exception as e:
        logger.warning(f"Google Finance search failed: {e}")
        return None

async def get_market_news(symbol: str, limit: int = 5) -> list:
    """
    Get recent news for a stock symbol
    """
    try:
        # This would integrate with news APIs
        # For now, return empty list
        logger.info(f"📰 Market news search for {symbol} (feature placeholder)")
        return []
        
    except Exception as e:
        logger.error(f"❌ News search failed for {symbol}: {e}")
        return []

async def search_earnings_date(symbol: str) -> Optional[str]:
    """
    Search for next earnings date for a stock
    """
    try:
        # This would search for earnings calendar data
        logger.info(f"📅 Earnings date search for {symbol} (feature placeholder)")
        return None
        
    except Exception as e:
        logger.error(f"❌ Earnings search failed for {symbol}: {e}")
        return None

# Test function
async def test_web_search():
    """Test the web search functionality"""
    test_symbols = ['AAPL', 'MSFT', 'SPY']
    
    for symbol in test_symbols:
        print(f"\n🔍 Testing search for {symbol}...")
        result = await search_stock_data(symbol)
        
        if result:
            print(f"✅ {symbol}: ${result['price']:.2f} ({result['change_pct']:+.2f}%)")
            print(f"   Volume: {result['volume']:,}")
            print(f"   Source: {result['source']}")
        else:
            print(f"❌ Failed to find data for {symbol}")

if __name__ == "__main__":
    asyncio.run(test_web_search()) 