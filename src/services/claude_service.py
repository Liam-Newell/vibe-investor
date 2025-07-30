"""
Claude AI Service for Options Trading Analysis
Handles individual position conversations and strategic analysis
"""

import asyncio
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import httpx
from anthropic import Anthropic, AsyncAnthropic
from pydantic import BaseModel

from src.core.config import settings
from src.models.options import (
    OptionsPosition, ClaudeDecision, ClaudeActionType, OptionContract,
    VolatilityData, GreeksData, PortfolioSummary
)

logger = logging.getLogger(__name__)

class MarketAssessment(BaseModel):
    """Claude's market assessment"""
    overall_sentiment: str
    volatility_environment: str
    opportunity_quality: str
    recommended_exposure: str

class CashStrategy(BaseModel):
    """Claude's cash management strategy"""
    action: str
    reasoning: str
    target_cash_percentage: float
    urgency: str

class EnhancedOptionsOpportunity(BaseModel):
    """Enhanced options opportunity with priority"""
    symbol: str
    strategy_type: str
    contracts: List[Dict[str, Any]]
    rationale: str
    confidence: float
    risk_assessment: str
    target_return: float
    max_risk: float
    time_horizon: int
    priority: str = "medium"

class MorningStrategyResponse(BaseModel):
    """Complete morning strategy response from Claude"""
    market_assessment: MarketAssessment
    cash_strategy: CashStrategy
    opportunities: List[EnhancedOptionsOpportunity]

class ClaudeResponse(BaseModel):
    """Structured Claude response for options analysis"""
    action: ClaudeActionType
    confidence: float
    reasoning: str
    market_outlook: str
    volatility_assessment: str
    risk_assessment: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    time_horizon: Optional[int] = None

class OptionsOpportunity(BaseModel):
    """Claude-identified options opportunity"""
    symbol: str
    strategy_type: str
    contracts: List[Dict[str, Any]]
    rationale: str
    confidence: float
    risk_assessment: str
    target_return: float
    max_risk: float
    time_horizon: int

class ClaudeService:
    """Claude AI service for options trading analysis"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = 2000
        self.daily_query_count = 0
        self.conversation_threads: Dict[str, List[Dict]] = {}
        
    async def health_check(self) -> bool:
        """Check if Claude API is accessible"""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except Exception as e:
            logger.error(f"Claude health check failed: {e}")
            return False
    
    async def test_json_response(self) -> Dict[str, Any]:
        """Test that Claude returns proper JSON format"""
        try:
            prompt = """
            RESPONSE FORMAT: Return ONLY valid JSON object. No additional text or markdown.
            
            Schema:
            {
              "status": "success",
              "message": "JSON parsing test completed",
              "confidence": 0.95,
              "timestamp": "2024-01-29T10:00:00Z"
            }
            
            Return a JSON object following this exact schema.
            """
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Test parsing
            response_text = response.content[0].text
            cleaned = response_text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            parsed_data = json.loads(cleaned)
            
            return {
                "success": True,
                "raw_response": response_text,
                "parsed_data": parsed_data,
                "message": "Claude JSON parsing test passed!"
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON parsing failed: {e}",
                "raw_response": response_text if 'response_text' in locals() else "No response",
                "message": "Claude is not returning valid JSON"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Claude API test failed"
            }
    
    async def morning_strategy_session(self, portfolio: PortfolioSummary, market_data: Dict[str, Any], earnings_calendar: List[Dict], current_positions: List) -> MorningStrategyResponse:
        """
        CLAUDE AUTONOMOUS TRADING: Claude picks everything independently
        
        Step 1: Claude autonomously selects stocks/options based on its knowledge
        Step 2: Get live data for Claude's autonomous picks  
        Step 3: Claude reviews live data and makes final decision with current context
        Step 4: Dynamic confidence filtering + autonomous execution
        
        No human input - Claude makes ALL trading decisions
        """
        if not self.client:
            await self._initialize_client()
            
        try:
            # STEP 1: Claude's autonomous trading picks (no proposals from us)
            logger.info("🤖 Step 1: Claude autonomously selecting trading opportunities...")
            initial_recommendations = await self._get_claude_initial_picks(portfolio, current_positions)
            
            if not initial_recommendations or len(initial_recommendations) == 0:
                logger.warning("⚠️ Claude provided no autonomous trading picks")
                return self._create_fallback_response()
            
            # Extract symbols from Claude's autonomous picks with validation
            recommended_symbols = []
            for rec in initial_recommendations:
                symbol = rec.get('symbol', '').strip().upper()
                if symbol and len(symbol) <= 10:  # Valid stock symbol length
                    recommended_symbols.append(symbol)
                else:
                    logger.warning(f"⚠️ Invalid symbol from Claude: {symbol}")
            
            if not recommended_symbols:
                logger.error("❌ No valid symbols from Claude's autonomous picks")
                return self._create_fallback_response()
            
            logger.info(f"📊 Claude autonomously picked symbols: {recommended_symbols}")
            
            # STEP 2: Get live market data for Claude's autonomous picks only
            logger.info("🔍 Step 2: Searching live data for Claude's autonomous stock picks...")
            live_market_data = await self._search_live_data_for_symbols(recommended_symbols)
            
            if not live_market_data:
                logger.warning("⚠️ No live market data found for Claude's picks")
                # Continue anyway - Claude can still make decisions with knowledge
            
            # STEP 3: Claude reviews live data and makes final autonomous decision
            logger.info("🤖 Step 3: Claude making final autonomous decision with live market context...")
            final_strategy_response = await self._get_claude_final_decision(
                portfolio, initial_recommendations, live_market_data, current_positions
            )
            
            if final_strategy_response:
                num_opportunities = len(final_strategy_response.opportunities)
                logger.info(f"🎯 Claude's final autonomous decision: {num_opportunities} confirmed opportunities")
                
                # Log Claude's autonomous analysis
                if hasattr(final_strategy_response, 'market_assessment'):
                    assessment = final_strategy_response.market_assessment
                    logger.info(f"📊 Claude's market sentiment: {assessment.overall_sentiment}")
                    if hasattr(assessment, 'key_observations'):
                        logger.info(f"📊 Claude's key observations: {assessment.key_observations}")
                
                return final_strategy_response
            else:
                logger.warning("⚠️ Claude changed mind after reviewing live data - no final picks")
                return self._create_fallback_response()
                
        except Exception as e:
            logger.error(f"❌ Claude autonomous trading process failed: {e}")
            return self._create_fallback_response()
    
    async def _get_claude_initial_picks(self, portfolio: PortfolioSummary, current_positions: List) -> List[Dict[str, Any]]:
        """Step 1: Claude autonomously picks stocks/options based on its knowledge"""
        try:
            prompt = f"""
            🤖 AUTONOMOUS OPTIONS TRADING PICKS
            
            You are an expert options trader. Based on your knowledge of the current market environment (early 2025), 
            independently select 3-6 specific options trading opportunities that you believe are good trades right now.
            
            CURRENT PORTFOLIO CONTEXT:
            • Portfolio value: ${portfolio.total_value:,.0f}
            • Cash available: ${portfolio.cash_balance:,.0f}
            • Open positions: {portfolio.open_positions}/{settings.MAX_SWING_POSITIONS}
            • Performance streak: {portfolio.performance_history.current_streak}
            • Recent win rate: {portfolio.performance_history.recent_win_rate:.1%}
            • Risk level: {portfolio.get_adaptive_risk_level()}
            
            CURRENT POSITIONS (avoid duplicates):
            {[f"{p.symbol} {p.strategy_type.value}" for p in current_positions]}
            
            YOUR TASK: AUTONOMOUSLY PICK GOOD OPTIONS TRADES
            
            GUIDELINES:
            1. Pick specific stocks/ETFs YOU believe have good options trading opportunities
            2. Choose from high-liquidity symbols (AAPL, MSFT, GOOGL, AMZN, TSLA, SPY, QQQ, NVDA, META, etc.)
            3. Consider what you know about:
               - Earnings seasons and cycles
               - Market seasonality patterns  
               - Technical setups and support/resistance levels
               - Volatility environments
               - Sector rotations and trends
            4. Mix different strategies based on your market outlook
            5. Factor in the portfolio's performance streak for risk management
            6. Avoid symbols already in current positions
            
            STRATEGY SELECTION (pick what YOU think is best):
            - Long calls: If you're bullish on a stock
            - Long puts: If you're bearish on a stock  
            - Credit spreads: If you want defined risk/reward
            - Iron condors: If you expect range-bound movement
            - Put spreads: If you're moderately bearish
            
            IMPORTANT: 
            - Make YOUR OWN decisions based on your knowledge
            - I will search for live market data on your picks
            - You'll get a chance to review current prices before final decision
            
            RETURN FORMAT - VALID JSON ONLY:
            [
                {{
                    "symbol": "AAPL",
                    "strategy_type": "long_call",
                    "initial_confidence": 0.75,
                    "rationale": "Strong iPhone demand and technical breakout expected",
                    "reasoning": "Detailed explanation of why this is a good trade",
                    "time_horizon": "3-4 weeks",
                    "expected_move": "bullish to $240"
                }},
                {{
                    "symbol": "SPY", 
                    "strategy_type": "iron_condor",
                    "initial_confidence": 0.68,
                    "rationale": "Market showing range-bound behavior, good premium collection",
                    "reasoning": "VIX elevated, expecting sideways movement",
                    "time_horizon": "2-3 weeks", 
                    "expected_move": "sideways 450-460"
                }}
            ]
            
            CRITICAL: Return ONLY valid JSON array. No other text, explanations, or markdown.
            Pick trades YOU genuinely believe in based on your market knowledge.
            """
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            logger.info(f"🤖 Claude provided autonomous trading picks")
            
            # Parse JSON response with better error handling
            try:
                import json
                
                # Clean the response - remove any markdown formatting
                content = content.replace('```json', '').replace('```', '').strip()
                
                # Find JSON array bounds
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    recommendations = json.loads(json_str)
                    
                    # Validate the structure
                    valid_recommendations = []
                    for rec in recommendations:
                        if self._validate_recommendation_structure(rec):
                            valid_recommendations.append(rec)
                        else:
                            logger.warning(f"⚠️ Invalid recommendation structure: {rec}")
                    
                    if valid_recommendations:
                        logger.info(f"✅ Claude autonomously picked {len(valid_recommendations)} trading opportunities")
                        for rec in valid_recommendations:
                            logger.info(f"   📊 {rec['symbol']} {rec['strategy_type']} (confidence: {rec.get('initial_confidence', 0):.1%})")
                        return valid_recommendations
                    else:
                        logger.warning("⚠️ No valid recommendations in Claude's response")
                        return []
                else:
                    logger.warning("⚠️ No valid JSON array found in Claude's response")
                    return []
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing error in Claude's autonomous picks: {e}")
                logger.error(f"Raw content: {content}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to get Claude's autonomous picks: {e}")
            return []
    
    def _validate_recommendation_structure(self, rec: Dict[str, Any]) -> bool:
        """Validate that Claude's recommendation has the required structure for live data search"""
        required_fields = ['symbol', 'strategy_type', 'initial_confidence']
        
        # Check required fields
        for field in required_fields:
            if field not in rec:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate symbol is string and not empty
        if not isinstance(rec['symbol'], str) or not rec['symbol'].strip():
            logger.warning(f"Invalid symbol: {rec.get('symbol')}")
            return False
        
        # Validate strategy type
        valid_strategies = ['long_call', 'long_put', 'credit_spread', 'iron_condor', 'put_spread', 'short_call', 'short_put']
        if rec['strategy_type'] not in valid_strategies:
            logger.warning(f"Invalid strategy type: {rec.get('strategy_type')}")
            return False
        
        # Validate confidence is numeric
        confidence = rec.get('initial_confidence')
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            logger.warning(f"Invalid confidence: {confidence}")
            return False
        
        return True
    
    async def _search_live_data_for_symbols(self, symbols: List[str]) -> Dict[str, Any]:
        """Step 2: Get live market data for Claude's recommended symbols"""
        try:
            # Import web search function
            from src.utils.web_search import search_stock_data
            
            live_data = {}
            
            for symbol in symbols:
                logger.info(f"🔍 Searching live data for {symbol}...")
                
                # Search for current stock data
                search_results = await search_stock_data(symbol)
                
                if search_results:
                    live_data[symbol] = search_results
                    logger.info(f"✅ Found live data for {symbol}: ${search_results.get('price', 'N/A')}")
                else:
                    logger.warning(f"⚠️ No live data found for {symbol}")
                    live_data[symbol] = {"error": "No live data available"}
            
            return live_data
            
        except ImportError:
            # Fallback: use our market data service
            logger.info("📊 Using market data service as fallback...")
            return await self._get_market_data_fallback(symbols)
        except Exception as e:
            logger.error(f"❌ Failed to search live data: {e}")
            return {}
    
    async def _get_market_data_fallback(self, symbols: List[str]) -> Dict[str, Any]:
        """Fallback: Use our market data service for live data"""
        try:
            from src.services.market_data_service import MarketDataService
            
            market_service = MarketDataService()
            await market_service.initialize()
            
            live_data = {}
            
            for symbol in symbols:
                try:
                    data = await market_service.get_market_data(symbol)
                    if data:
                        live_data[symbol] = {
                            "price": data.price,
                            "change_pct": data.change_pct,
                            "volume": data.volume,
                            "bid": data.bid,
                            "ask": data.ask,
                            "timestamp": data.timestamp.isoformat()
                        }
                        logger.info(f"✅ Market data for {symbol}: ${data.price:.2f} ({data.change_pct:+.2f}%)")
                    else:
                        live_data[symbol] = {"error": "No data available"}
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get data for {symbol}: {e}")
                    live_data[symbol] = {"error": str(e)}
            
            await market_service.close()
            return live_data
            
        except Exception as e:
            logger.error(f"❌ Market data fallback failed: {e}")
            return {}
    
    async def _get_claude_final_decision(self, portfolio: PortfolioSummary, initial_recommendations: List[Dict], live_data: Dict[str, Any], current_positions: List) -> Optional[MorningStrategyResponse]:
        """Step 3: Claude reviews live data for its own autonomous picks and makes final decision"""
        try:
            # Format live data for Claude
            live_data_summary = self._format_live_data_for_claude(live_data)
            
            prompt = f"""
            🤖 FINAL AUTONOMOUS TRADING DECISION WITH LIVE MARKET DATA
            
            Earlier, you autonomously selected these options trading opportunities:
            {json.dumps(initial_recommendations, indent=2)}
            
            Here is the LIVE MARKET DATA for YOUR selected symbols:
            {live_data_summary}
            
            PORTFOLIO CONTEXT:
            • Portfolio value: ${portfolio.total_value:,.0f}
            • Cash available: ${portfolio.cash_balance:,.0f}
            • Performance streak: {portfolio.performance_history.current_streak}
            • Risk level: {portfolio.get_adaptive_risk_level()}
            
            YOUR AUTONOMOUS DECISION:
            Looking at the live market data for YOUR selected stocks, do you want to proceed with these trades?
            You can:
            1. Confirm your picks with specific position details
            2. Modify some based on current prices/conditions  
            3. Remove any that no longer look attractive
            4. Recommend holding cash if current conditions don't support your ideas
            
            RESPONSE FORMAT (JSON ONLY):
            {{
                "market_assessment": {{
                    "overall_sentiment": "Your autonomous assessment of current market conditions",
                    "key_observations": "What the live data tells you about your selected symbols",
                    "recommended_exposure": "Conservative/Normal/Aggressive"
                }},
                "cash_strategy": {{
                    "action": "DEPLOY/PARTIAL_DEPLOY/HOLD_CASH",
                    "percentage": 70,
                    "reasoning": "Why this allocation makes sense given live conditions"
                }},
                "opportunities": [
                    {{
                        "symbol": "AAPL",
                        "strategy_type": "long_call",
                        "confidence": 0.78,
                        "target_return": 1500.0,
                        "max_risk": 1200.0,
                        "time_horizon_days": 21,
                        "strike_price": 230.0,
                        "rationale": "Updated rationale with live market context",
                        "entry_criteria": "Specific entry conditions",
                        "exit_criteria": "Profit target and stop loss",
                        "live_data_validation": "How current price/volume supports YOUR trade idea"
                    }}
                ]
            }}
            
            CRITICAL: Base your final autonomous decision on the LIVE market data for YOUR picks.
            If the current prices don't support your original ideas, modify or remove them.
            Only proceed with opportunities that still make sense given current market conditions.
            These are YOUR autonomous trading decisions - make the best choices.
            """
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            logger.info(f"🤖 Claude reviewed live data for its autonomous picks")
            
            # Parse the final response
            parsed_response = self._parse_live_morning_response(content)
            
            if parsed_response:
                logger.info(f"✅ Claude confirmed {len(parsed_response.opportunities)} autonomous opportunities after live data review")
                return parsed_response
            else:
                logger.warning("⚠️ Failed to parse Claude's final autonomous decision")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get Claude's final autonomous decision: {e}")
            return None
    
    def _format_live_data_for_claude(self, live_data: Dict[str, Any]) -> str:
        """Format live market data in a readable way for Claude"""
        formatted = "LIVE MARKET DATA:\n"
        
        for symbol, data in live_data.items():
            if "error" in data:
                formatted += f"• {symbol}: ❌ {data['error']}\n"
            else:
                price = data.get('price', 'N/A')
                change = data.get('change_pct', 0)
                volume = data.get('volume', 0)
                
                formatted += f"• {symbol}: ${price:.2f} ({change:+.2f}%) | Volume: {volume:,}\n"
        
        return formatted
    
    async def analyze_position(self, 
                             position: OptionsPosition,
                             market_data: Dict[str, Any],
                             portfolio_context: PortfolioSummary) -> Optional[ClaudeDecision]:
        """
        Individual position analysis with Claude
        Maintains conversation thread for each position
        """
        logger.info(f"🔍 Analyzing position {position.id} ({position.symbol})")
        
        if self.daily_query_count >= settings.CLAUDE_MAX_DAILY_QUERIES:
            logger.warning("Daily Claude query limit reached")
            return None
        
        # Get or create conversation thread
        conversation_id = position.claude_conversation_id
        if conversation_id not in self.conversation_threads:
            self.conversation_threads[conversation_id] = []
        
        # Prepare position context
        context = self._prepare_position_context(position, market_data, portfolio_context)
        
        # Check if this is first analysis or follow-up
        is_followup = len(self.conversation_threads[conversation_id]) > 0
        
        if is_followup:
            prompt = f"""
            Following up on our previous analysis of {position.symbol} position.
            
            Position Update:
            {context['position_update']}
            
            Current Market Data:
            {context['market_update']}
            
            Time Since Last Check: {self._time_since_last_check(position)}
            
            Key Changes Since Last Analysis:
            {context['changes']}
            
            RESPONSE FORMAT: Return ONLY valid JSON object. No additional text or markdown.
            
            Schema:
            {{
              "action": "HOLD",
              "confidence": 0.85,
              "reasoning": "Detailed explanation for the decision...",
              "market_outlook": "Bullish/Bearish/Neutral with reasoning",
              "volatility_assessment": "Current IV analysis and expectations",
              "risk_assessment": "Risk level and management considerations",
              "target_price": 155.0,
              "stop_loss": 145.0,
              "time_horizon": 14
            }}
            
            Action options: HOLD, CLOSE, ADJUST_STOP, ADJUST_TARGET, ROLL_OPTION, ADD_POSITION
            
            Analysis Requirements:
            - Current P&L: {position.pnl_percentage:.1f}%
            - Days to expiration: {min(c.days_to_expiration for c in position.contracts)}
            - Time decay impact (theta)
            - Volatility changes
            - Portfolio risk impact
            """
        else:
            prompt = f"""
            Initial analysis for new {position.symbol} options position.
            
            Position Details:
            {context['position_details']}
            
            Market Analysis:
            {context['market_analysis']}
            
            Portfolio Context:
            {context['portfolio_context']}
            
            RESPONSE FORMAT: Return ONLY valid JSON object. No additional text or markdown.
            
            Schema:
            {{
              "action": "HOLD",
              "confidence": 0.85,
              "reasoning": "Initial assessment of the position setup and market conditions...",
              "market_outlook": "Bullish/Bearish/Neutral with reasoning",
              "volatility_assessment": "Current IV analysis and expectations",
              "risk_assessment": "Risk level and management plan",
              "target_price": 155.0,
              "stop_loss": 145.0,
              "time_horizon": 14
            }}
            
            Action options: HOLD, CLOSE, ADJUST_STOP, ADJUST_TARGET, ROLL_OPTION
            
            Analysis Requirements:
            - Initial risk assessment and Greeks impact
            - Target exit strategy and key levels
            - Timeline for next check-in
            - How position fits within portfolio limits
            """
        
        try:
            response = await self._query_claude_conversation(prompt, conversation_id)
            decision = self._parse_position_response(response, position.id, conversation_id)
            self.daily_query_count += 1
            
            # Update conversation thread
            self.conversation_threads[conversation_id].append({
                "timestamp": datetime.utcnow().isoformat(),
                "prompt": prompt,
                "response": response,
                "decision": decision.dict() if decision else None
            })
            
            logger.info(f"✅ Position analysis complete. Action: {decision.action if decision else 'None'}")
            return decision
            
        except Exception as e:
            logger.error(f"❌ Position analysis failed: {e}")
            return None
    
    async def evening_review_session(self,
                                   portfolio: PortfolioSummary,
                                   positions: List[OptionsPosition],
                                   daily_trades: List[Dict],
                                   market_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evening Claude review session for performance analysis and tomorrow's strategy
        """
        logger.info("🌆 Starting evening Claude review session")
        
        if self.daily_query_count >= settings.CLAUDE_MAX_DAILY_QUERIES:
            logger.warning("Daily Claude query limit reached")
            return {}
        
        context = self._prepare_evening_context(portfolio, positions, daily_trades, market_summary)
        
        prompt = f"""
        End-of-day portfolio review and analysis.
        
        Today's Performance:
        {context['performance']}
        
        Position Analysis:
        {context['positions']}
        
        Trades Executed Today:
        {context['trades']}
        
        Market Summary:
        {context['market']}
        
        Portfolio Greeks Summary:
        - Delta: {portfolio.total_delta}
        - Gamma: {portfolio.total_gamma}
        - Theta: {portfolio.total_theta} (daily decay)
        - Vega: {portfolio.total_vega}
        
        Please provide:
        1. Performance attribution analysis (what drove P&L)
        2. Risk assessment of current portfolio
        3. Positions requiring attention tomorrow
        4. Strategy adjustments for tomorrow
        5. Market outlook for next trading session
        6. Lessons learned from today's trading
        
        Focus on:
        - Greeks management and risk exposure
        - Upcoming expirations and time decay
        - Volatility changes and their impact
        - Position adjustments needed
        """
        
        try:
            response = await self._query_claude(prompt, "evening_review")
            review = self._parse_evening_response(response)
            self.daily_query_count += 1
            
            logger.info("✅ Evening review session complete")
            return review
            
        except Exception as e:
            logger.error(f"❌ Evening review session failed: {e}")
            return {}
    
    async def emergency_analysis(self, 
                                trigger: str,
                                position: OptionsPosition,
                                market_data: Dict[str, Any]) -> Optional[ClaudeDecision]:
        """
        Emergency Claude analysis for significant position moves
        """
        logger.warning(f"🚨 Emergency analysis triggered: {trigger}")
        
        # Reserve queries for emergencies
        if self.daily_query_count >= settings.CLAUDE_MAX_DAILY_QUERIES - 2:
            logger.error("Cannot perform emergency analysis - query limit reached")
            return None
        
        context = self._prepare_emergency_context(trigger, position, market_data)
        
        prompt = f"""
        EMERGENCY POSITION ANALYSIS
        
        Trigger: {trigger}
        
        Position Status:
        {context['position']}
        
        Market Conditions:
        {context['market']}
        
        URGENT: This position requires immediate attention.
        
        Current P&L: {position.pnl_percentage:.1f}%
        Days to expiration: {min(c.days_to_expiration for c in position.contracts)}
        
        Provide immediate recommendation:
        1. HOLD - Position is still viable
        2. CLOSE - Exit immediately
        3. ADJUST - Modify position parameters
        4. HEDGE - Add protective position
        
        Consider:
        - Risk of further losses
        - Time decay acceleration
        - Volatility impact
        - Liquidity for exit
        
        This is time-sensitive. Provide clear, actionable guidance.
        """
        
        try:
            response = await self._query_claude(prompt, "emergency")
            decision = self._parse_position_response(response, position.id, position.claude_conversation_id)
            self.daily_query_count += 1
            
            logger.warning(f"🚨 Emergency analysis complete. Action: {decision.action if decision else 'None'}")
            return decision
            
        except Exception as e:
            logger.error(f"❌ Emergency analysis failed: {e}")
            return None
    
    async def get_position_management_advice(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get Claude's advice for position management and exit decisions"""
        try:
            if not self.client:
                await self._initialize_client()
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for more consistent decisions
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = response.content[0].text.strip()
            
            # Try to parse JSON response
            try:
                import json
                # Extract JSON from response if it's wrapped in other text
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # Validate response structure
                    if 'action' in result and 'reasoning' in result:
                        logger.info(f"🤖 Claude position advice: {result['action']} ({result.get('confidence', 0):.1%})")
                        return result
                
            except json.JSONDecodeError:
                logger.warning("⚠️ Could not parse Claude's JSON response for position management")
            
            # Fallback: try to extract action from text
            content_lower = content.lower()
            if 'close' in content_lower or 'sell' in content_lower or 'exit' in content_lower:
                return {
                    "action": "CLOSE",
                    "confidence": 0.6,
                    "reasoning": "Text analysis suggests closing position"
                }
            else:
                return {
                    "action": "HOLD",
                    "confidence": 0.6, 
                    "reasoning": "Text analysis suggests holding position"
                }
                
        except Exception as e:
            logger.error(f"❌ Claude position management advice failed: {e}")
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "reasoning": f"Error in analysis: {str(e)}"
            }
    
    def cleanup_conversation(self, conversation_id: str):
        """Clean up conversation thread when position is closed"""
        if conversation_id in self.conversation_threads:
            del self.conversation_threads[conversation_id]
            logger.info(f"🧹 Cleaned up conversation thread: {conversation_id}")
    
    def reset_daily_count(self):
        """Reset daily query count (called at start of new trading day)"""
        self.daily_query_count = 0
        logger.info("🔄 Reset daily Claude query count")
    
    # Private helper methods
    async def _query_claude(self, prompt: str, session_type: str) -> str:
        """Make API call to Claude"""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error ({session_type}): {e}")
            raise
    
    async def _query_claude_conversation(self, prompt: str, conversation_id: str) -> str:
        """Query Claude with conversation context"""
        messages = []
        
        # Add conversation history
        if conversation_id in self.conversation_threads:
            for entry in self.conversation_threads[conversation_id][-3:]:  # Last 3 exchanges
                messages.append({"role": "user", "content": entry["prompt"]})
                messages.append({"role": "assistant", "content": entry["response"]})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude conversation API error: {e}")
            raise
    
    def _prepare_morning_context(self, portfolio, market_data, earnings_calendar, positions) -> Dict[str, str]:
        """Prepare context for morning session with enhanced performance tracking"""
        return {
            "portfolio": json.dumps({
                "total_value": portfolio.total_value,
                "cash_balance": portfolio.cash_balance,
                "open_positions": portfolio.open_positions,
                "total_delta": portfolio.total_delta,
                "total_vega": portfolio.total_vega,
                "total_pnl": portfolio.total_pnl,
                "win_rate": portfolio.win_rate,
                "max_drawdown": portfolio.max_drawdown
            }, indent=2),
            "performance_history": json.dumps({
                "last_7_days_pnl": portfolio.performance_history.last_7_days_pnl,
                "last_30_days_pnl": portfolio.performance_history.last_30_days_pnl,
                "last_60_days_pnl": portfolio.performance_history.last_60_days_pnl,
                "current_streak": portfolio.performance_history.current_streak,
                "consecutive_losses": portfolio.performance_history.consecutive_losses,
                "days_since_last_win": portfolio.performance_history.days_since_last_win,
                "recent_win_rate": portfolio.performance_history.recent_win_rate,
                "performance_trend": portfolio.performance_history.performance_trend,
                "risk_confidence": portfolio.performance_history.risk_confidence,
                "strategy_performance": portfolio.performance_history.strategy_performance
            }, indent=2),
            "risk_assessment": json.dumps({
                "current_risk_level": portfolio.get_adaptive_risk_level(),
                "risk_adjusted_confidence": portfolio.risk_adjusted_confidence,
                "suggested_position_size_multiplier": portfolio.suggested_position_size_multiplier,
                "portfolio_utilization": portfolio.portfolio_utilization
            }, indent=2),
            "market": json.dumps(market_data, indent=2),
            "earnings": json.dumps(earnings_calendar, indent=2),
            "positions": json.dumps([{
                "symbol": p.symbol,
                "strategy": p.strategy_type,
                "pnl": p.pnl_percentage,
                "days_held": p.days_held
            } for p in positions], indent=2)
        }
    
    def _prepare_position_context(self, position, market_data, portfolio) -> Dict[str, str]:
        """Prepare context for position analysis"""
        return {
            "position_details": json.dumps({
                "symbol": position.symbol,
                "strategy": position.strategy_type,
                "entry_cost": position.entry_cost,
                "current_value": position.current_value,
                "pnl_pct": position.pnl_percentage,
                "days_held": position.days_held,
                "contracts": [c.dict() for c in position.contracts]
            }, indent=2),
            "market_analysis": json.dumps(market_data, indent=2),
            "portfolio_context": json.dumps({
                "total_delta": portfolio.total_delta,
                "total_vega": portfolio.total_vega,
                "utilization": portfolio.portfolio_utilization
            }, indent=2)
        }
    
    def _parse_morning_response(self, response: str) -> MorningStrategyResponse:
        """Parse Claude's enhanced morning strategy response"""
        try:
            # Clean response - remove any markdown or extra text
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Parse JSON directly
            data = json.loads(cleaned)
            
            # Validate it's an object with required keys
            if not isinstance(data, dict):
                logger.error(f"Expected object, got {type(data)}")
                return self._create_fallback_response()
            
            required_keys = ['market_assessment', 'cash_strategy', 'opportunities']
            for key in required_keys:
                if key not in data:
                    logger.error(f"Missing required key: {key}")
                    return self._create_fallback_response()
            
            # Parse and validate the response
            try:
                morning_response = MorningStrategyResponse(**data)
                logger.info(f"✅ Parsed enhanced strategy: {len(morning_response.opportunities)} opportunities, "
                           f"cash strategy: {morning_response.cash_strategy.action}, "
                           f"market sentiment: {morning_response.market_assessment.overall_sentiment}")
                return morning_response
            except Exception as e:
                logger.error(f"Failed to validate response structure: {e}")
                return self._create_fallback_response()
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response content: {response[:500]}...")
        except Exception as e:
            logger.error(f"Failed to parse morning response: {e}")
        
        return self._create_fallback_response()
    
    def _create_fallback_response(self) -> MorningStrategyResponse:
        """Create a conservative fallback response when parsing fails"""
        return MorningStrategyResponse(
            market_assessment=MarketAssessment(
                overall_sentiment="uncertain",
                volatility_environment="elevated",
                opportunity_quality="poor",
                recommended_exposure="minimal"
            ),
            cash_strategy=CashStrategy(
                action="hold_cash",
                reasoning="Unable to parse Claude response - holding cash for safety",
                target_cash_percentage=90.0,
                urgency="high"
            ),
            opportunities=[]
        )
    
    def _parse_position_response(self, response: str, position_id: UUID, conversation_id: str) -> Optional[ClaudeDecision]:
        """Parse Claude's position analysis response"""
        try:
            # Clean response - remove any markdown or extra text
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Parse JSON directly
            data = json.loads(cleaned)
            
            # Validate required fields
            required_fields = ['action', 'confidence', 'reasoning', 'market_outlook', 
                             'volatility_assessment', 'risk_assessment']
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            # Convert action string to enum
            try:
                action = ClaudeActionType(data['action'])
            except ValueError:
                logger.error(f"Invalid action: {data['action']}")
                return None
            
            # Create ClaudeDecision object
            return ClaudeDecision(
                position_id=position_id,
                conversation_id=conversation_id,
                action=action,
                confidence=float(data['confidence']),
                reasoning=data['reasoning'],
                market_outlook=data['market_outlook'],
                volatility_assessment=data['volatility_assessment'],
                risk_assessment=data['risk_assessment'],
                target_price=data.get('target_price'),
                stop_loss=data.get('stop_loss'),
                time_horizon=data.get('time_horizon')
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response content: {response[:500]}...")
        except Exception as e:
            logger.error(f"Failed to parse position response: {e}")
            
        return None
    
    def _parse_evening_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude's evening review response"""
        return {
            "summary": response,
            "performance_attribution": {},
            "risk_assessment": {},
            "tomorrow_strategy": {},
            "lessons_learned": []
        }
    
    def _time_since_last_check(self, position: OptionsPosition) -> str:
        """Calculate time since last Claude check"""
        if not position.last_claude_check:
            return "First analysis"
        
        delta = datetime.utcnow() - position.last_claude_check
        hours = delta.total_seconds() / 3600
        return f"{hours:.1f} hours ago"
    
    def _prepare_evening_context(self, portfolio, positions, trades, market) -> Dict[str, str]:
        """Prepare context for evening review"""
        return {
            "performance": json.dumps({
                "total_pnl": portfolio.total_pnl,
                "win_rate": portfolio.win_rate,
                "open_positions": portfolio.open_positions
            }, indent=2),
            "positions": json.dumps([{
                "symbol": p.symbol,
                "pnl": p.pnl_percentage,
                "status": p.status
            } for p in positions], indent=2),
            "trades": json.dumps(trades, indent=2),
            "market": json.dumps(market, indent=2)
        }
    
    def _prepare_emergency_context(self, trigger, position, market_data) -> Dict[str, str]:
        """Prepare context for emergency analysis"""
        return {
            "position": json.dumps({
                "symbol": position.symbol,
                "pnl": position.pnl_percentage,
                "current_value": position.current_value,
                "days_to_exp": min(c.days_to_expiration for c in position.contracts)
            }, indent=2),
            "market": json.dumps(market_data, indent=2)
        } 

    def _prepare_live_market_context(self, portfolio: PortfolioSummary, market_data: Dict[str, Any], earnings_calendar: List[Dict], positions: List) -> Dict[str, str]:
        """Prepare comprehensive live market context for Claude analysis"""
        
        # Format live market data
        live_market_summary = f"""
        REAL-TIME MARKET DATA:
        • SPY: ${market_data.get('spy_price', 'N/A')} ({market_data.get('spy_change', 0):+.2f}%)
        • QQQ: ${market_data.get('qqq_price', 'N/A')} ({market_data.get('qqq_change', 0):+.2f}%)
        • VIX: {market_data.get('vix', 'N/A')} ({market_data.get('vix_change', 0):+.2f}%)
        • Dollar Index: {market_data.get('dollar_index', 'N/A')}
        
        MARKET SENTIMENT: {market_data.get('market_sentiment', 'Unknown')}
        VOLATILITY TREND: {market_data.get('volatility_trend', 'Unknown')}
        MARKET HOURS: {'OPEN' if market_data.get('market_hours', False) else 'CLOSED'}
        DATA SOURCE: {market_data.get('data_source', 'Live')}
        
        SECTOR PERFORMANCE (Live ETF Data):
        """
        
        # Add sector performance if available
        sector_performance = market_data.get('sector_performance', {})
        for sector, performance in sector_performance.items():
            live_market_summary += f"• {sector}: {performance:+.2f}%\n"
        
        return {
            "live_market": live_market_summary,
            "portfolio": json.dumps({
                "total_value": portfolio.total_value,
                "cash_balance": portfolio.cash_balance,
                "open_positions": portfolio.open_positions,
                "total_pnl": portfolio.total_pnl,
                "win_rate": portfolio.win_rate,
                "max_drawdown": portfolio.max_drawdown,
                "portfolio_utilization": portfolio.portfolio_utilization
            }, indent=2),
            "performance_history": json.dumps({
                "current_streak": portfolio.performance_history.current_streak,
                "consecutive_losses": portfolio.performance_history.consecutive_losses,
                "days_since_last_win": portfolio.performance_history.days_since_last_win,
                "recent_win_rate": portfolio.performance_history.recent_win_rate,
                "last_7_days_pnl": portfolio.performance_history.last_7_days_pnl,
                "last_30_days_pnl": portfolio.performance_history.last_30_days_pnl,
                "performance_trend": portfolio.performance_history.performance_trend,
                "risk_confidence": portfolio.performance_history.risk_confidence
            }, indent=2),
            "risk_assessment": json.dumps({
                "current_risk_level": portfolio.get_adaptive_risk_level(),
                "risk_adjusted_confidence": portfolio.risk_adjusted_confidence,
                "suggested_position_size_multiplier": portfolio.suggested_position_size_multiplier,
                "adaptive_thresholds_active": True
            }, indent=2),
            "positions": json.dumps([{
                "symbol": p.symbol,
                "strategy": p.strategy_type.value,
                "pnl": getattr(p, 'unrealized_pnl', 0),
                "days_held": (datetime.now() - p.entry_date).days if hasattr(p, 'entry_date') else 0,
                "current_value": getattr(p, 'current_value', 0)
            } for p in positions], indent=2),
            "earnings": json.dumps(earnings_calendar, indent=2) if earnings_calendar else "No major earnings this week"
        }
    
    def _parse_live_morning_response(self, content: str) -> Optional[MorningStrategyResponse]:
        """Parse Claude's live market analysis response"""
        try:
            # Extract JSON from response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)
                
                # Validate required structure
                if not all(key in data for key in ['market_assessment', 'cash_strategy', 'opportunities']):
                    logger.warning("⚠️ Missing required keys in Claude's response")
                    return None
                
                # Parse market assessment
                market_assessment = MarketAssessment(**data['market_assessment'])
                
                # Parse cash strategy
                cash_strategy = CashStrategy(**data['cash_strategy'])
                
                # Parse opportunities
                opportunities = []
                for opp_data in data['opportunities']:
                    try:
                        opportunity = EnhancedOptionsOpportunity(**opp_data)
                        opportunities.append(opportunity)
                    except Exception as e:
                        logger.warning(f"⚠️ Skipping invalid opportunity: {e}")
                        continue
                
                logger.info(f"✅ Successfully parsed {len(opportunities)} live opportunities from Claude")
                
                return MorningStrategyResponse(
                    market_assessment=market_assessment,
                    cash_strategy=cash_strategy,
                    opportunities=opportunities
                )
                
            else:
                logger.warning("⚠️ No valid JSON found in Claude's response")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error in live response: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing live morning response: {e}")
            return None 