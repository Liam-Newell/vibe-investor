"""
Market Data Service - Live Data Integration
Provides real-time market data from live sources for position valuation and market analysis
"""

import logging
import asyncio
import aiohttp
import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd

from src.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class MarketDataPoint:
    """Live market data for a single symbol"""
    symbol: str
    price: float
    volume: int
    change_pct: float
    timestamp: datetime
    bid: float
    ask: float
    implied_volatility: Optional[float] = None
    high_52week: Optional[float] = None
    low_52week: Optional[float] = None
    avg_volume: Optional[int] = None

@dataclass
class OptionQuote:
    """Live option chain quote data"""
    symbol: str
    underlying_price: float
    strike: float
    expiration: datetime
    option_type: str  # 'call' or 'put'
    bid: float
    ask: float
    last_price: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float

class MarketDataService:
    """Live market data service with real API integrations"""
    
    def __init__(self):
        self.market_data_cache: Dict[str, MarketDataPoint] = {}
        self.option_quotes_cache: Dict[str, List[OptionQuote]] = {}
        self.last_update = None
        self.session = None
        
        # API configuration
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY if hasattr(settings, 'ALPHA_VANTAGE_API_KEY') else None
        self.polygon_key = settings.POLYGON_API_KEY if hasattr(settings, 'POLYGON_API_KEY') else None
        
        # Market hours (Eastern Time)
        self.market_open_hour = 9
        self.market_open_minute = 30
        self.market_close_hour = 16
        self.market_close_minute = 0
    
    async def initialize(self):
        """Initialize HTTP session for API calls"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            logger.info("📡 Market data service initialized with live data feeds")
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    def is_market_hours(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        
        # Check if weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check time (simplified - not accounting for holidays)
        market_open = now.replace(hour=self.market_open_hour, minute=self.market_open_minute, second=0)
        market_close = now.replace(hour=self.market_close_hour, minute=self.market_close_minute, second=0)
        
        return market_open <= now <= market_close
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get live current price for a symbol using Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different price fields
            price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
            
            if price:
                return float(price)
            
            # Fallback: get from history
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            
            logger.warning(f"⚠️ No price data available for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get live price for {symbol}: {e}")
            return None
    
    async def get_market_data(self, symbol: str) -> Optional[MarketDataPoint]:
        """Get complete live market data for a symbol"""
        try:
            await self.initialize()
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d", interval="1d")
            
            if hist.empty:
                logger.warning(f"⚠️ No historical data for {symbol}")
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            previous_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
            
            change_pct = ((current_price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
            
            market_data = MarketDataPoint(
                symbol=symbol,
                price=current_price,
                volume=int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0,
                change_pct=change_pct,
                timestamp=datetime.now(),
                bid=info.get('bid', current_price - 0.01),
                ask=info.get('ask', current_price + 0.01),
                implied_volatility=None,  # Would need options data
                high_52week=info.get('fiftyTwoWeekHigh'),
                low_52week=info.get('fiftyTwoWeekLow'),
                avg_volume=info.get('averageVolume')
            )
            
            # Cache the data
            self.market_data_cache[symbol] = market_data
            
            logger.debug(f"📊 Live data for {symbol}: ${current_price:.2f} ({change_pct:+.2f}%)")
            
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get live market data for {symbol}: {e}")
            return None
    
    async def get_option_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get live option chain data for a symbol"""
        try:
            await self.initialize()
            
            ticker = yf.Ticker(symbol)
            
            # Get available expiration dates
            expirations = ticker.options
            
            if not expirations:
                logger.warning(f"⚠️ No option expirations available for {symbol}")
                return None
            
            # Get nearest expiration (usually most liquid)
            nearest_exp = expirations[0]
            
            # Get option chain for nearest expiration
            opt_chain = ticker.option_chain(nearest_exp)
            
            calls = opt_chain.calls
            puts = opt_chain.puts
            
            # Get underlying price
            underlying_price = await self.get_current_price(symbol)
            
            if underlying_price is None:
                return None
            
            option_data = {
                "symbol": symbol,
                "underlying_price": underlying_price,
                "expiration": nearest_exp,
                "calls": calls.to_dict('records') if not calls.empty else [],
                "puts": puts.to_dict('records') if not puts.empty else []
            }
            
            logger.info(f"📊 Retrieved option chain for {symbol}: {len(calls)} calls, {len(puts)} puts")
            
            return option_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get option chain for {symbol}: {e}")
            return None
    
    async def get_option_price(self, symbol: str, strike: float, expiration: datetime, option_type: str) -> Optional[float]:
        """Get live option price from option chain"""
        try:
            # Get option chain data
            chain_data = await self.get_option_chain(symbol)
            
            if not chain_data:
                return None
            
            # Look for matching option in chain
            options_list = chain_data['calls'] if option_type.lower() == 'call' else chain_data['puts']
            
            # Find closest strike match
            best_match = None
            min_strike_diff = float('inf')
            
            for option in options_list:
                strike_diff = abs(option.get('strike', 0) - strike)
                if strike_diff < min_strike_diff:
                    min_strike_diff = strike_diff
                    best_match = option
            
            if best_match:
                # Use last price, or average of bid/ask
                last_price = best_match.get('lastPrice')
                bid = best_match.get('bid', 0)
                ask = best_match.get('ask', 0)
                
                if last_price and last_price > 0:
                    return float(last_price)
                elif bid > 0 and ask > 0:
                    return float((bid + ask) / 2)
                elif ask > 0:
                    return float(ask)
            
            logger.warning(f"⚠️ No matching option found for {symbol} {strike} {option_type}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get live option price: {e}")
            return None
    
    async def get_vix_level(self) -> float:
        """Get current VIX level"""
        try:
            vix_data = await self.get_market_data("^VIX")
            return vix_data.price if vix_data else 20.0
        except:
            return 20.0
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """Get comprehensive live market summary"""
        try:
            # Get key market indicators
            spy_data = await self.get_market_data("SPY")
            qqq_data = await self.get_market_data("QQQ")
            vix_data = await self.get_market_data("^VIX")
            dxy_data = await self.get_market_data("DX-Y.NYB")  # Dollar index
            
            # Determine market sentiment based on real data
            market_sentiment = self._analyze_market_sentiment(spy_data, vix_data)
            volatility_trend = self._analyze_volatility_trend(vix_data)
            
            return {
                "spy_price": spy_data.price if spy_data else None,
                "spy_change": spy_data.change_pct if spy_data else None,
                "qqq_price": qqq_data.price if qqq_data else None,
                "qqq_change": qqq_data.change_pct if qqq_data else None,
                "vix": vix_data.price if vix_data else None,
                "vix_change": vix_data.change_pct if vix_data else None,
                "dollar_index": dxy_data.price if dxy_data else None,
                "market_sentiment": market_sentiment,
                "volatility_trend": volatility_trend,
                "market_hours": self.is_market_hours(),
                "last_updated": datetime.now().isoformat(),
                "data_source": "Live Yahoo Finance",
                "sector_performance": await self._get_sector_performance()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get live market summary: {e}")
            return {"error": str(e), "data_source": "Live Data Error"}
    
    def _analyze_market_sentiment(self, spy_data: Optional[MarketDataPoint], vix_data: Optional[MarketDataPoint]) -> str:
        """Analyze market sentiment from live data"""
        if not spy_data or not vix_data:
            return "Unknown"
        
        # VIX-based sentiment
        if vix_data.price < 12:
            sentiment = "Extremely Bullish"
        elif vix_data.price < 16:
            sentiment = "Bullish"
        elif vix_data.price < 20:
            sentiment = "Neutral-Bullish"
        elif vix_data.price < 25:
            sentiment = "Neutral"
        elif vix_data.price < 30:
            sentiment = "Cautious"
        elif vix_data.price < 40:
            sentiment = "Bearish"
        else:
            sentiment = "Extremely Bearish"
        
        # Adjust based on SPY movement
        if spy_data.change_pct > 2.0:
            sentiment += " (Strong Rally)"
        elif spy_data.change_pct < -2.0:
            sentiment += " (Sharp Decline)"
        elif abs(spy_data.change_pct) > 1.0:
            sentiment += f" ({'Up' if spy_data.change_pct > 0 else 'Down'} {abs(spy_data.change_pct):.1f}%)"
        
        return sentiment
    
    def _analyze_volatility_trend(self, vix_data: Optional[MarketDataPoint]) -> str:
        """Analyze volatility trend"""
        if not vix_data:
            return "Unknown"
        
        vix_level = vix_data.price
        vix_change = vix_data.change_pct
        
        if vix_level < 15:
            base = "Low volatility"
        elif vix_level < 20:
            base = "Normal volatility"
        elif vix_level < 30:
            base = "Elevated volatility"
        else:
            base = "High volatility"
        
        if vix_change > 10:
            trend = f"{base} - Spiking higher"
        elif vix_change > 5:
            trend = f"{base} - Rising"
        elif vix_change < -10:
            trend = f"{base} - Collapsing"
        elif vix_change < -5:
            trend = f"{base} - Declining"
        else:
            trend = f"{base} - Stable"
        
        return trend
    
    async def _get_sector_performance(self) -> Dict[str, float]:
        """Get live sector ETF performance"""
        sector_etfs = {
            "Technology": "XLK",
            "Financials": "XLF", 
            "Healthcare": "XLV",
            "Energy": "XLE",
            "Utilities": "XLU",
            "Real Estate": "XLRE",
            "Materials": "XLB",
            "Industrials": "XLI",
            "Consumer Discretionary": "XLY",
            "Consumer Staples": "XLP",
            "Communication": "XLC"
        }
        
        sector_performance = {}
        
        try:
            for sector, etf in sector_etfs.items():
                data = await self.get_market_data(etf)
                if data:
                    sector_performance[sector] = data.change_pct
                    
        except Exception as e:
            logger.error(f"❌ Failed to get sector performance: {e}")
        
        return sector_performance
    
    async def get_earnings_calendar(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get earnings calendar for next N days (simplified - would integrate with real earnings API)"""
        # This would integrate with real earnings data providers like:
        # - Alpha Vantage Earnings API
        # - Financial Modeling Prep
        # - Polygon.io earnings endpoint
        
        logger.info(f"🗓️ Earnings calendar integration needed for {days_ahead} days ahead")
        
        # For now, return empty list - in production, implement real earnings API
        return []
    
    async def update_all_cached_data(self):
        """Update all cached market data with live feeds"""
        try:
            # Get list of symbols from existing cache
            symbols_to_update = list(self.market_data_cache.keys())
            
            # Add essential market symbols if not present
            essential_symbols = ["SPY", "QQQ", "^VIX", "DX-Y.NYB"]
            for symbol in essential_symbols:
                if symbol not in symbols_to_update:
                    symbols_to_update.append(symbol)
            
            update_count = 0
            for symbol in symbols_to_update:
                data = await self.get_market_data(symbol)
                if data:
                    update_count += 1
            
            self.last_update = datetime.now()
            logger.info(f"📊 Updated {update_count} symbols with live market data")
            
        except Exception as e:
            logger.error(f"❌ Failed to update live market data: {e}") 