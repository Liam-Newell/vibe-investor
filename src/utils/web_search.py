"""
Enhanced Web Search Utility for Claude AI
Provides comprehensive web search capabilities for market analysis and stock research
"""

import logging
import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class WebSearchService:
    """Enhanced web search service for comprehensive market research"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=30))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def comprehensive_stock_research(self, symbol: str) -> Dict[str, Any]:
        """
        Comprehensive stock research using multiple sources
        Returns detailed market data, news, and analysis
        """
        try:
            results = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'price_data': None,
                'news': [],
                'earnings': None,
                'technical_analysis': None,
                'market_sentiment': None,
                'sources': []
            }
            
            # Parallel data collection
            tasks = [
                self._get_price_data(symbol),
                self._get_stock_news(symbol),
                self._get_earnings_info(symbol),
                self._get_technical_analysis(symbol),
                self._get_market_sentiment(symbol)
            ]
            
            price_data, news, earnings, technical, sentiment = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            if not isinstance(price_data, Exception) and price_data:
                results['price_data'] = price_data
                results['sources'].append('Yahoo Finance')
            
            if not isinstance(news, Exception) and news:
                results['news'] = news[:10]  # Limit to 10 most recent
                results['sources'].append('News APIs')
            
            if not isinstance(earnings, Exception) and earnings:
                results['earnings'] = earnings
                results['sources'].append('Earnings Calendar')
            
            if not isinstance(technical, Exception) and technical:
                results['technical_analysis'] = technical
                results['sources'].append('Technical Analysis')
            
            if not isinstance(sentiment, Exception) and sentiment:
                results['market_sentiment'] = sentiment
                results['sources'].append('Market Sentiment')
            
            logger.info(f"✅ Comprehensive research completed for {symbol} using {len(results['sources'])} sources")
            return results
            
        except Exception as e:
            logger.error(f"❌ Comprehensive research failed for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def _get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive price data from Yahoo Finance"""
        try:
            # Multiple Yahoo Finance endpoints for comprehensive data
            endpoints = [
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=price,summaryDetail,defaultKeyStatistics,financialData"
            ]
            
            for endpoint in endpoints:
                try:
                    async with self.session.get(endpoint) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if 'chart' in data and data['chart']['result']:
                                # Chart data
                                result = data['chart']['result'][0]
                                meta = result.get('meta', {})
                                
                                current_price = meta.get('regularMarketPrice')
                                previous_close = meta.get('previousClose', current_price)
                                
                                if current_price and previous_close:
                                    change_pct = ((current_price - previous_close) / previous_close) * 100
                                    
                                    return {
                                        'current_price': current_price,
                                        'previous_close': previous_close,
                                        'change_pct': change_pct,
                                        'volume': meta.get('regularMarketVolume', 0),
                                        'market_cap': meta.get('marketCap'),
                                        'pe_ratio': meta.get('trailingPE'),
                                        'currency': meta.get('currency', 'USD'),
                                        'market_state': meta.get('marketState', 'UNKNOWN'),
                                        'source': 'Yahoo Finance'
                                    }
                            
                            elif 'quoteSummary' in data and data['quoteSummary']['result']:
                                # Quote summary data
                                result = data['quoteSummary']['result'][0]
                                price = result.get('price', {})
                                summary = result.get('summaryDetail', {})
                                
                                current_price = price.get('regularMarketPrice', {}).get('raw')
                                previous_close = price.get('regularMarketPreviousClose', {}).get('raw')
                                
                                if current_price and previous_close:
                                    change_pct = ((current_price - previous_close) / previous_close) * 100
                                    
                                    return {
                                        'current_price': current_price,
                                        'previous_close': previous_close,
                                        'change_pct': change_pct,
                                        'volume': price.get('regularMarketVolume', {}).get('raw', 0),
                                        'market_cap': summary.get('marketCap', {}).get('raw'),
                                        'pe_ratio': summary.get('trailingPE', {}).get('raw'),
                                        'currency': price.get('currency', 'USD'),
                                        'market_state': price.get('marketState', 'UNKNOWN'),
                                        'source': 'Yahoo Finance'
                                    }
                
                except Exception as e:
                    logger.warning(f"Yahoo Finance endpoint failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Price data search failed for {symbol}: {e}")
            return None
    
    async def _get_stock_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Get recent news for a stock symbol"""
        try:
            # Try multiple news sources
            news_sources = [
                self._get_yahoo_news,
                self._get_alpha_vantage_news,
                self._get_market_watch_news
            ]
            
            all_news = []
            for news_func in news_sources:
                try:
                    news = await news_func(symbol)
                    if news:
                        all_news.extend(news)
                except Exception as e:
                    logger.warning(f"News source {news_func.__name__} failed: {e}")
                    continue
            
            # Remove duplicates and sort by date
            unique_news = []
            seen_titles = set()
            
            for news_item in all_news:
                title = news_item.get('title', '').lower()
                if title not in seen_titles:
                    seen_titles.add(title)
                    unique_news.append(news_item)
            
            # Sort by date (newest first)
            unique_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            
            return unique_news[:15]  # Return top 15 unique news items
            
        except Exception as e:
            logger.warning(f"News search failed for {symbol}: {e}")
            return []
    
    async def _get_yahoo_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Get news from Yahoo Finance"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}/news"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'news' in data and data['news']:
                        news_items = []
                        for item in data['news']:
                            news_items.append({
                                'title': item.get('title', ''),
                                'summary': item.get('summary', ''),
                                'url': item.get('url', ''),
                                'published_at': item.get('published_at', ''),
                                'source': 'Yahoo Finance'
                            })
                        return news_items
            
            return []
            
        except Exception as e:
            logger.warning(f"Yahoo news failed: {e}")
            return []
    
    async def _get_alpha_vantage_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Get news from Alpha Vantage (if API key available)"""
        # This would require an Alpha Vantage API key
        # For now, return empty list
        return []
    
    async def _get_market_watch_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Get news from MarketWatch (simplified)"""
        # This would require web scraping
        # For now, return empty list
        return []
    
    async def _get_earnings_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get earnings information"""
        try:
            url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=calendarEvents,earnings"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'quoteSummary' in data and data['quoteSummary']['result']:
                        result = data['quoteSummary']['result'][0]
                        
                        earnings = result.get('earnings', {})
                        calendar = result.get('calendarEvents', {})
                        
                        return {
                            'next_earnings_date': earnings.get('earningsDate', [{}])[0].get('fmt'),
                            'earnings_estimate': earnings.get('earningsAverage', {}).get('raw'),
                            'revenue_estimate': earnings.get('revenueAverage', {}).get('raw'),
                            'calendar_events': calendar.get('earnings', {}),
                            'source': 'Yahoo Finance'
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"Earnings info failed for {symbol}: {e}")
            return None
    
    async def _get_technical_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get technical analysis indicators"""
        try:
            # Get historical data for technical analysis
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=30d"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'chart' in data and data['chart']['result']:
                        result = data['chart']['result'][0]
                        timestamps = result.get('timestamp', [])
                        closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                        
                        if len(closes) >= 20:
                            # Calculate simple moving averages
                            sma_20 = sum(closes[-20:]) / 20
                            sma_10 = sum(closes[-10:]) / 10
                            current_price = closes[-1]
                            
                            # Calculate RSI (simplified)
                            gains = [max(0, closes[i] - closes[i-1]) for i in range(1, len(closes))]
                            losses = [max(0, closes[i-1] - closes[i]) for i in range(1, len(closes))]
                            
                            avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else 0
                            avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else 0
                            
                            if avg_loss > 0:
                                rs = avg_gain / avg_loss
                                rsi = 100 - (100 / (1 + rs))
                            else:
                                rsi = 100
                            
                            return {
                                'sma_20': sma_20,
                                'sma_10': sma_10,
                                'current_price': current_price,
                                'rsi': rsi,
                                'trend': 'bullish' if sma_10 > sma_20 else 'bearish',
                                'source': 'Yahoo Finance'
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"Technical analysis failed for {symbol}: {e}")
            return None
    
    async def _get_market_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market sentiment indicators"""
        try:
            # This would integrate with sentiment analysis APIs
            # For now, return basic sentiment based on price movement
            price_data = await self._get_price_data(symbol)
            
            if price_data and price_data.get('change_pct'):
                change_pct = price_data['change_pct']
                
                if change_pct > 2:
                    sentiment = 'very_bullish'
                elif change_pct > 0.5:
                    sentiment = 'bullish'
                elif change_pct > -0.5:
                    sentiment = 'neutral'
                elif change_pct > -2:
                    sentiment = 'bearish'
                else:
                    sentiment = 'very_bearish'
                
                return {
                    'sentiment': sentiment,
                    'confidence': min(abs(change_pct) / 5, 1.0),  # Higher confidence for larger moves
                    'price_change_pct': change_pct,
                    'source': 'Price Movement Analysis'
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Market sentiment failed for {symbol}: {e}")
            return None

# Legacy functions for backward compatibility
async def search_stock_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Legacy function - now uses enhanced search service"""
    async with WebSearchService() as search_service:
        result = await search_service.comprehensive_stock_research(symbol)
        if result and 'price_data' in result and result['price_data']:
            return result['price_data']
        return None

async def get_market_news(symbol: str, limit: int = 5) -> list:
    """Legacy function - now uses enhanced search service"""
    async with WebSearchService() as search_service:
        result = await search_service.comprehensive_stock_research(symbol)
        if result and 'news' in result:
            return result['news'][:limit]
        return []

async def search_earnings_date(symbol: str) -> Optional[str]:
    """Legacy function - now uses enhanced search service"""
    async with WebSearchService() as search_service:
        result = await search_service.comprehensive_stock_research(symbol)
        if result and 'earnings' in result and result['earnings']:
            return result['earnings'].get('next_earnings_date')
        return None

# Test function
async def test_enhanced_web_search():
    """Test the enhanced web search functionality"""
    test_symbols = ['AAPL', 'MSFT', 'SPY']
    
    async with WebSearchService() as search_service:
        for symbol in test_symbols:
            print(f"\n🔍 Testing enhanced search for {symbol}...")
            result = await search_service.comprehensive_stock_research(symbol)
            
            if result and 'error' not in result:
                print(f"✅ {symbol}: Comprehensive research completed")
                print(f"   Sources: {', '.join(result['sources'])}")
                
                if result['price_data']:
                    price_data = result['price_data']
                    print(f"   Price: ${price_data['current_price']:.2f} ({price_data['change_pct']:+.2f}%)")
                
                if result['news']:
                    print(f"   News: {len(result['news'])} articles found")
                
                if result['earnings']:
                    print(f"   Earnings: {result['earnings'].get('next_earnings_date', 'N/A')}")
                
                if result['technical_analysis']:
                    tech = result['technical_analysis']
                    print(f"   Technical: {tech['trend']} (RSI: {tech['rsi']:.1f})")
                
                if result['market_sentiment']:
                    sentiment = result['market_sentiment']
                    print(f"   Sentiment: {sentiment['sentiment']} ({sentiment['confidence']:.1%})")
            else:
                print(f"❌ Failed to research {symbol}: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_web_search()) 