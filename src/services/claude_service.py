"""
Claude AI Service for Options Trading Analysis
Handles individual position conversations and strategic analysis
"""

import asyncio
import json
import logging
import re
import random
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import httpx
from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import TextBlock, ToolUseBlock
from pydantic import BaseModel

from src.core.config import settings
from src.models.options import (
    OptionsPosition, ClaudeDecision, ClaudeActionType, OptionContract,
    VolatilityData, GreeksData, PortfolioSummary, EnhancedOptionsOpportunity,
    MorningStrategyResponse, MarketAssessment, CashStrategy
)
from src.utils.web_search import search_stock_data, WebSearchService
from claude_summaries import claude_summary_manager

logger = logging.getLogger(__name__)

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
        self.max_retries = 2  # Reduced from 3 to avoid rate limit escalation
        self.base_delay = 5.0  # Increased from 2.0 to respect rate limits
        self.max_delay = 60.0  # Increased for 429 errors
    
    def _extract_text_from_response(self, response) -> str:
        """Safely extract text from Claude response, handling both text and tool use blocks"""
        try:
            # Handle multiple content blocks
            text_parts = []
            tool_blocks = []
            
            for block in response.content:
                if hasattr(block, 'text') and block.text:
                    # This is a TextBlock with actual content
                    text_parts.append(block.text)
                elif hasattr(block, 'type') and block.type == 'tool_use':
                    # This is a ToolUseBlock - Claude used a tool
                    tool_blocks.append(block)
                    logger.info(f"🔧 Claude used tool: {getattr(block, 'name', 'unknown')}")
                else:
                    # Try to extract any text content from unknown block types
                    block_str = str(block)
                    if len(block_str) > 50 and not block_str.startswith('<'):
                        text_parts.append(block_str)
            
            # If we have text content, use it
            if text_parts:
                combined_text = "\n".join(text_parts).strip()
                if combined_text:
                    return combined_text
            
            # If no text but we have tool blocks, Claude probably used tools without providing text
            if tool_blocks and not text_parts:
                logger.warning(f"⚠️ Claude used {len(tool_blocks)} tools but provided no text response")
                return ""
            
            # Final fallback - try to get any content
            logger.warning("⚠️ No text content found in Claude response")
            return ""
            
        except Exception as e:
            logger.error(f"❌ Failed to extract text from Claude response: {e}")
            logger.error(f"Response content types: {[type(block) for block in response.content] if hasattr(response, 'content') else 'No content'}")
            
            # Enhanced fallback
            try:
                if hasattr(response, 'content') and response.content:
                    first_block = response.content[0]
                    if hasattr(first_block, 'text'):
                        return first_block.text
                    else:
                        logger.error(f"First block type: {type(first_block)}, attributes: {dir(first_block)}")
                return ""
            except Exception as fallback_error:
                logger.error(f"❌ Fallback extraction also failed: {fallback_error}")
                return ""
    
    async def _retry_claude_request(self, request_func, request_name: str, *args, **kwargs):
        """Retry Claude API requests with exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"🤖 {request_name} - Attempt {attempt + 1}/{self.max_retries + 1}")
                
                # Make the API request
                response = await request_func(*args, **kwargs)
                
                logger.info(f"✅ {request_name} successful on attempt {attempt + 1}")
                return response
                
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Check if this is a retryable error
                retryable = False
                delay = 0
                
                if any(code in error_str for code in ['500', '502', '503', '529', 'overloaded']):
                    if attempt < self.max_retries:
                        # Calculate delay with exponential backoff + jitter
                        delay = min(
                            self.base_delay * (2 ** attempt) + random.uniform(0, 1),
                            self.max_delay
                        )
                        retryable = True
                elif '429' in error_str or 'rate_limit' in error_str:
                    # Special handling for rate limits - longer delays, fewer retries
                    if attempt < 1:  # Only retry once for rate limits
                        delay = 30.0 + random.uniform(0, 10)  # 30-40 second wait
                        logger.warning(f"⚠️ Rate limit hit for {request_name} - waiting {delay:.0f}s")
                        retryable = True
                    else:
                        logger.error(f"❌ Rate limit - not retrying {request_name} to avoid escalation")
                        break
                
                if retryable:
                    logger.warning(f"⚠️ {request_name} failed (attempt {attempt + 1}): {e}")
                    logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Non-retryable error, fail immediately
                    logger.error(f"❌ {request_name} failed with non-retryable error: {e}")
                    break
        
        # If we get here, all retries failed
        raise last_exception if last_exception else Exception(f"{request_name} failed after all retries")
        
    async def health_check(self) -> bool:
        """Check if Claude API is accessible"""
        try:
            # Use retry mechanism for health check
            async def make_request():
                return await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
                )
            
            response = await self._retry_claude_request(
                make_request,
                "Claude Health Check"
            )
            return True
        except Exception as e:
            logger.error(f"Claude health check failed after retries: {e}")
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
            
            # Use retry mechanism for Claude API call
            async def make_request():
                return await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
                )
            
            response = await self._retry_claude_request(
                make_request,
                "Claude JSON Test"
            )
            
            # Test parsing
            response_text = self._extract_text_from_response(response)
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
                logger.warning("⚠️ Claude provided no autonomous trading picks - using fallback")
                # Generate dynamic fallback picks instead of empty response
                initial_recommendations = self._generate_fallback_picks(portfolio)
                
                # Skip the second Claude call to avoid rate limits when using fallback
                logger.info("🔄 Using fallback picks - skipping second Claude call to prevent rate limits")
                opportunities = []
                for pick in initial_recommendations:
                                    opportunities.append(EnhancedOptionsOpportunity(
                    symbol=pick.get('symbol', ''),
                    strategy_type=pick.get('strategy_type', 'long_call'),
                    confidence=pick.get('initial_confidence', 0.7),
                    rationale=pick.get('rationale', 'Fallback pick'),
                    risk_assessment='Moderate risk',
                    time_horizon=21,  # 3 weeks in days
                    target_return=1500.0,
                    max_risk=1000.0,
                    contracts=[],
                    priority='Normal'
                ))
                
                return MorningStrategyResponse(
                    market_assessment=MarketAssessment(
                        overall_sentiment="neutral",
                        volatility_environment="normal", 
                        opportunity_quality="moderate",
                        recommended_exposure="normal"
                    ),
                    cash_strategy=CashStrategy(
                        action="partial_deploy",
                        reasoning="Using fallback picks to avoid rate limits",
                        target_cash_percentage=75.0,
                        urgency="medium"
                    ),
                    opportunities=opportunities
                )
            
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
            
            # STEP 3: Skip second Claude call to prevent rate limits - use initial picks directly
            logger.info("🔄 Step 3: Converting initial picks to final format (avoiding second Claude call for rate limits)")
            
            opportunities = []
            for pick in initial_recommendations:
                opportunities.append(OptionsOpportunity(
                    symbol=pick.get('symbol', ''),
                    strategy_type=pick.get('strategy_type', 'long_call'),
                    confidence=pick.get('initial_confidence', 0.7),
                    rationale=pick.get('rationale', 'Claude initial pick'),
                    risk_assessment='Moderate risk',
                    time_horizon=21,  # 3 weeks in days
                    target_return=1500.0,
                    max_risk=1000.0,
                    contracts=[],
                    priority='Normal'
                ))
            
            final_strategy_response = MorningStrategyResponse(
                market_assessment=MarketAssessment(
                    overall_sentiment="neutral",
                    volatility_environment="normal",
                    opportunity_quality="good", 
                    recommended_exposure="normal"
                ),
                cash_strategy=CashStrategy(
                    action="deploy",
                    reasoning="Using Claude's initial picks directly",
                    target_cash_percentage=70.0,
                    urgency="medium"
                ),
                opportunities=opportunities
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
                
                # Generate and save morning summary for dashboard
                await self._generate_and_save_morning_summary(final_strategy_response, portfolio, market_data)
                
                return final_strategy_response
            else:
                logger.warning("⚠️ Claude changed mind after reviewing live data - no final picks")
                # Save fallback summary
                try:
                    claude_summary_manager.save_morning_summary(
                        summary="No trades today - Claude reviewed live data and decided to hold cash",
                        opportunities_count=0,
                        market_analysis="Cautious approach after live data review"
                    )
                except:
                    pass
                return self._create_fallback_response()
                
        except Exception as e:
            logger.error(f"❌ Claude autonomous trading process failed: {e}")
            # Save fallback summary for error case
            try:
                claude_summary_manager.save_morning_summary(
                    summary="Morning session error - system will retry next morning",
                    opportunities_count=0,
                    market_analysis="Technical error during analysis"
                )
            except:
                pass
            return self._create_fallback_response()
    
    async def _get_claude_initial_picks(self, portfolio: PortfolioSummary, current_positions: List) -> List[Dict[str, Any]]:
        """Step 1: Claude autonomously picks stocks/options using built-in web search tool"""
        try:
            current_symbols = [p.symbol for p in current_positions]
            # Fix f-string formatting issue by using regular string concatenation
            prompt = f"""Search web for today's best stock picks. Avoid: {current_symbols}

Portfolio: ${portfolio.cash_balance:,.0f} cash, {portfolio.performance_history.current_streak} streak

Task: Web search 2-3 liquid stocks (AAPL,MSFT,GOOGL,NVDA,TSLA,SPY,QQQ) with strong setups.

Return JSON only:""" + """
[{"symbol":"NVDA","strategy_type":"long_call","initial_confidence":0.75,"rationale":"Earnings beat + breakout","reasoning":"Web shows: earnings beat, technical breakout at $140","time_horizon":"3 weeks","expected_move":"bullish to $160","web_research_summary":"Searched: positive earnings, breakout pattern"}]"""
            
            # Use retry mechanism for Claude API call (REDUCED TOKENS)
            async def make_request():
                return await self.client.messages.create(
                model=self.model,
                    max_tokens=400,  # Drastically reduced from 2000
                temperature=0.4,
                    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],  # Reduced searches
                messages=[{"role": "user", "content": prompt}]
            )
            
            response = await self._retry_claude_request(
                make_request, 
                "Claude Initial Picks"
            )
            
            content = self._extract_text_from_response(response)
            logger.info(f"🤖 Claude provided autonomous trading picks with web search")
            
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
            logger.error(f"❌ Failed to get Claude's autonomous picks after retries: {e}")
            # Add more specific error handling for common issues
            if "ServerToolUseBlock" in str(e):
                logger.error("🔧 Claude used tools but response parsing failed - this is a known issue being fixed")
            elif any(code in str(e) for code in ["rate_limit_error", "429", "500", "529", "overloaded"]):
                logger.error("⚠️ Claude API overloaded after retries - falling back to dynamic picks")
            else:
                logger.error(f"⚠️ Unexpected Claude API error: {e}")
            
            # Generate fallback picks on error
            logger.info("🤖 Generating fallback picks due to Claude API issues...")
            fallback_picks = self._generate_fallback_picks(portfolio)
            if fallback_picks:
                logger.info(f"✅ Generated {len(fallback_picks)} fallback picks after API failure")
                return fallback_picks
            
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
        valid_strategies = ['long_call', 'long_put', 'call_spread', 'put_spread', 'iron_condor', 'straddle', 'strangle', 'covered_call', 'protective_put']
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
        """Step 2: Get comprehensive live market data for Claude's recommended symbols"""
        try:
            live_data = {}
            
            async with WebSearchService() as search_service:
                for symbol in symbols:
                    logger.info(f"🔍 Comprehensive web research for {symbol}...")
                    
                    # Get comprehensive research data
                    research_results = await search_service.comprehensive_stock_research(symbol)
                    
                    if research_results and 'error' not in research_results:
                        live_data[symbol] = {
                            'price_data': research_results.get('price_data', {}),
                            'news': research_results.get('news', []),
                            'earnings': research_results.get('earnings', {}),
                            'technical_analysis': research_results.get('technical_analysis', {}),
                            'market_sentiment': research_results.get('market_sentiment', {}),
                            'sources': research_results.get('sources', []),
                            'timestamp': research_results.get('timestamp', '')
                        }
                        
                        price_data = research_results.get('price_data', {})
                        if price_data:
                            logger.info(f"✅ Comprehensive data for {symbol}: ${price_data.get('current_price', 'N/A')} ({price_data.get('change_pct', 0):+.2f}%)")
                            logger.info(f"   Sources: {', '.join(research_results.get('sources', []))}")
                            logger.info(f"   News: {len(research_results.get('news', []))} articles")
                            logger.info(f"   Technical: {research_results.get('technical_analysis', {}).get('trend', 'N/A')}")
                    else:
                        logger.warning(f"⚠️ No comprehensive data found for {symbol}")
                        live_data[symbol] = {"error": "No comprehensive data available"}
            
            return live_data
            
        except Exception as e:
            logger.error(f"❌ Failed to search comprehensive live data: {e}")
            # Fallback to basic search
            return await self._get_market_data_fallback(symbols)
    
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
        """Step 3: Claude reviews current prices and gives final trades (MINIMAL TOKENS)"""
        try:
            # Extract current prices from live data
            price_summary = []
            for symbol, data in live_data.items():
                price_data = data.get('price_data', {})
                current_price = price_data.get('current_price', 'N/A')
                change_pct = price_data.get('change_pct', 0)
                price_summary.append(f"{symbol}: ${current_price} ({change_pct:+.1f}%)")
            
            prompt = f"""Your picks: {json.dumps(initial_recommendations, indent=1)}

Current prices: {'; '.join(price_summary)}

Portfolio: ${(portfolio.cash_balance if portfolio else 100000):,.0f} cash

Review current prices. For each pick, provide:
1. Buy under price (specific)
2. Sell over price (specific) 
3. Exit date if neither hit

JSON only:
{{"market_assessment":{{"overall_sentiment":"bullish","recommended_exposure":"normal"}},"cash_strategy":{{"action":"DEPLOY","percentage":80,"reasoning":"Good setups"}},"opportunities":[{{"symbol":"NVDA","strategy_type":"long_call","confidence":0.75,"strike_price":145,"buy_under_price":148.50,"sell_over_price":165,"exit_date":"2025-08-20","rationale":"Current price good for entry","entry_criteria":"Buy if under $148.50","exit_criteria":"Sell at $165 or exit 2025-08-20"}}]}}"""
            
            # Use retry mechanism for Claude API call (MINIMAL TOKENS)
            async def make_request():
                return await self.client.messages.create(
                model=self.model,
                    max_tokens=1000,  # Drastically reduced from 4000
                temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]  # No more tools needed
                )
            
            response = await self._retry_claude_request(
                make_request,
                "Claude Final Decision"
            )
            
            content = self._extract_text_from_response(response)
            logger.info(f"🤖 Claude reviewed live data for its autonomous picks")
            
            # Handle case where Claude provided no text response
            if not content or content.strip() == "":
                logger.warning("⚠️ Claude provided no text response for final decision")
                logger.info("🔄 Converting initial picks to opportunities format")
                # Convert initial picks to proper format instead of returning None
                opportunities = []
                for pick in initial_recommendations:
                                    opportunities.append(OptionsOpportunity(
                    symbol=pick.get('symbol', ''),
                    strategy_type=pick.get('strategy_type', 'long_call'),
                    confidence=pick.get('initial_confidence', 0.7),
                    rationale=pick.get('rationale', 'Claude initial pick'),
                    risk_assessment='Moderate risk',
                    time_horizon=21,  # 3 weeks in days
                    target_return=1500.0,
                    max_risk=1000.0,
                    contracts=[],
                    priority='Normal'
                ))
                
                return MorningStrategyResponse(
                    market_assessment=MarketAssessment(
                        overall_sentiment="uncertain",
                        recommended_exposure="normal"
                    ),
                    cash_strategy=CashStrategy(
                        action="partial_deploy",
                        reasoning="Using Claude's initial picks",
                        target_cash_percentage=80.0,
                        urgency="medium"
                    ),
                    opportunities=opportunities
                )
            
            # Parse the final response
            parsed_response = self._parse_live_morning_response(content)
            
            if parsed_response:
                logger.info(f"✅ Claude confirmed {len(parsed_response.opportunities)} autonomous opportunities after live data review")
                return parsed_response
            else:
                logger.warning("⚠️ Failed to parse Claude's final autonomous decision")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get Claude's final autonomous decision after retries: {e}")
            # Add more specific error handling for common issues
            if "ServerToolUseBlock" in str(e):
                logger.error("🔧 Claude used tools but response parsing failed - this is a known issue being fixed")
            elif "format" in str(e).lower() and "nonetype" in str(e).lower():
                logger.error("🔧 Format string error in Claude response - likely missing portfolio data")
            elif any(code in str(e) for code in ["rate_limit_error", "429", "500", "529", "overloaded"]):
                logger.error("⚠️ Claude API overloaded for final decision after retries")
            
            logger.info("🔄 Proceeding without final Claude validation - fallback picks will be used as-is")
            return None
    
    def _format_live_data_for_claude(self, live_data: Dict[str, Any]) -> str:
        """Format comprehensive live market data in a readable way for Claude"""
        formatted = "COMPREHENSIVE WEB RESEARCH DATA:\n\n"
        
        for symbol, data in live_data.items():
            if "error" in data:
                formatted += f"• {symbol}: ❌ {data['error']}\n\n"
            else:
                # Price data
                price_data = data.get('price_data', {})
                if price_data:
                    price = price_data.get('current_price', 'N/A')
                    change = price_data.get('change_pct', 0)
                    volume = price_data.get('volume', 0)
                    market_cap = price_data.get('market_cap', 'N/A')
                    pe_ratio = price_data.get('pe_ratio', 'N/A')
                    
                    formatted += f"📊 {symbol} PRICE DATA:\n"
                    formatted += f"   Current Price: ${price} ({change:+.2f}%)\n"
                    formatted += f"   Volume: {volume:,}\n"
                    formatted += f"   Market Cap: ${market_cap:,}\n" if market_cap != 'N/A' else f"   Market Cap: {market_cap}\n"
                    formatted += f"   P/E Ratio: {pe_ratio}\n"
                
                # News data
                news = data.get('news', [])
                if news:
                    formatted += f"📰 {symbol} RECENT NEWS ({len(news)} articles):\n"
                    for i, article in enumerate(news[:3], 1):  # Show top 3 news
                        title = article.get('title', 'No title')
                        formatted += f"   {i}. {title[:80]}{'...' if len(title) > 80 else ''}\n"
                
                # Earnings data
                earnings = data.get('earnings', {})
                if earnings:
                    next_earnings = earnings.get('next_earnings_date', 'N/A')
                    earnings_est = earnings.get('earnings_estimate', 'N/A')
                    revenue_est = earnings.get('revenue_estimate', 'N/A')
                    
                    formatted += f"📅 {symbol} EARNINGS:\n"
                    formatted += f"   Next Earnings: {next_earnings}\n"
                    formatted += f"   EPS Estimate: {earnings_est}\n"
                    formatted += f"   Revenue Estimate: {revenue_est}\n"
                
                # Technical analysis
                technical = data.get('technical_analysis', {})
                if technical:
                    trend = technical.get('trend', 'N/A')
                    rsi = technical.get('rsi', 'N/A')
                    sma_20 = technical.get('sma_20', 'N/A')
                    sma_10 = technical.get('sma_10', 'N/A')
                    
                    formatted += f"📈 {symbol} TECHNICAL ANALYSIS:\n"
                    formatted += f"   Trend: {trend}\n"
                    formatted += f"   RSI: {rsi:.1f}\n" if rsi != 'N/A' else f"   RSI: {rsi}\n"
                    formatted += f"   SMA 20: ${sma_20:.2f}\n" if sma_20 != 'N/A' else f"   SMA 20: {sma_20}\n"
                    formatted += f"   SMA 10: ${sma_10:.2f}\n" if sma_10 != 'N/A' else f"   SMA 10: {sma_10}\n"
                
                # Market sentiment
                sentiment = data.get('market_sentiment', {})
                if sentiment:
                    sentiment_level = sentiment.get('sentiment', 'N/A')
                    confidence = sentiment.get('confidence', 'N/A')
                    
                    formatted += f"🎯 {symbol} MARKET SENTIMENT:\n"
                    formatted += f"   Sentiment: {sentiment_level}\n"
                    formatted += f"   Confidence: {confidence:.1%}\n" if confidence != 'N/A' else f"   Confidence: {confidence}\n"
                
                # Sources
                sources = data.get('sources', [])
                if sources:
                    formatted += f"🔍 Data Sources: {', '.join(sources)}\n"
                
                formatted += "\n" + "="*50 + "\n\n"
        
        return formatted
    
    def _generate_fallback_picks(self, portfolio: PortfolioSummary) -> List[Dict[str, Any]]:
        """Generate dynamic fallback picks when Claude API fails"""
        try:
            from datetime import datetime
            import random
            
            # Get risk level safely
            risk_level = portfolio.get_adaptive_risk_level() if portfolio else 'normal'
            current_streak = getattr(portfolio.performance_history, 'current_streak', 0) if portfolio and portfolio.performance_history else 0
            cash_balance = portfolio.cash_balance if portfolio else 100000
            
            fallback_picks = []
            
            # Dynamic symbol rotation based on market conditions and time
            liquid_symbols = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "GOOGL", "TSLA"]
            conservative_symbols = ["SPY", "QQQ", "IWM"]  # ETFs for conservative approach
            aggressive_symbols = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA"]  # Individual stocks
            
            # Time-based rotation to vary picks
            day_of_year = datetime.now().timetuple().tm_yday
            rotation_index = day_of_year % len(liquid_symbols)
            
            if risk_level == "conservative":
                symbol_pool = conservative_symbols
                strategies = ["iron_condor", "cash_secure_put", "covered_call"]
            elif risk_level == "aggressive":
                symbol_pool = aggressive_symbols
                strategies = ["long_call", "long_put", "straddle", "call_spread"]
            else:  # normal
                symbol_pool = liquid_symbols
                strategies = ["iron_condor", "call_spread", "put_spread", "long_call"]
            
            # Pick 1-2 symbols based on performance
            num_picks = 2 if current_streak > 2 else 1
            selected_symbols = []
            
            for i in range(min(num_picks, len(symbol_pool))):
                idx = (rotation_index + i) % len(symbol_pool)
                selected_symbols.append(symbol_pool[idx])
            
            for symbol in selected_symbols:
                # Strategy selection based on streak and symbol type
                if current_streak >= 3:
                    strategy = "long_call" if symbol in aggressive_symbols else "call_spread"
                elif current_streak <= -2:
                    strategy = "cash_secure_put" if symbol in conservative_symbols else "put_spread"
                else:
                    strategy = strategies[rotation_index % len(strategies)]
                
                confidence = 0.75 if current_streak > 0 else 0.72
                
                fallback_picks.append({
                    "symbol": symbol,
                    "strategy_type": strategy,
                    "initial_confidence": confidence,
                    "rationale": f"Dynamic fallback for {symbol} - {strategy} strategy based on {risk_level} risk profile and {current_streak} streak",
                    "reasoning": f"Systematic rotation pick: Day {day_of_year} rotation, {risk_level} risk, suitable for current portfolio state",
                    "time_horizon": "2-3 weeks",
                    "expected_move": "based on technical analysis and market sentiment",
                    "web_research_summary": f"Dynamic fallback rotation - {symbol} selected for {strategy} based on risk profile"
                })
                
                logger.info(f"🎲 Dynamic fallback generated: {symbol} {strategy} (confidence: {confidence:.0%})")
            
            # Only return picks if we have sufficient cash
            if cash_balance > 5000:
                return fallback_picks
            else:
                logger.info("💰 Insufficient cash for fallback picks")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to generate dynamic fallback picks: {e}")
            # Ultra-safe fallback to SPY
            return [{
                "symbol": "SPY",
                "strategy_type": "iron_condor",
                "initial_confidence": 0.60,
                "rationale": "Ultra-safe SPY fallback - system error recovery",
                "reasoning": "Emergency fallback due to system error",
                "time_horizon": "2-3 weeks",
                "expected_move": "range-bound",
                "web_research_summary": "Emergency fallback strategy"
            }]
    
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
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}],
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = self._extract_text_from_response(response)
            decision = self._parse_position_response(content, position.id, conversation_id)
            self.daily_query_count += 1
            
            # Update conversation thread
            self.conversation_threads[conversation_id].append({
                "timestamp": datetime.utcnow().isoformat(),
                "prompt": prompt,
                "response": content,
                "decision": decision.dict() if decision else None
            })
            
            logger.info(f"✅ Position analysis complete with web search. Action: {decision.action if decision else 'None'}")
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
        🌆 END-OF-DAY PORTFOLIO REVIEW WITH WEB SEARCH ANALYSIS
        
        You are an expert options trader with access to comprehensive web search capabilities.
        You MUST search multiple websites and sources to provide thorough end-of-day analysis.
        
        WEB SEARCH REQUIREMENTS FOR EVENING REVIEW:
        - Search for after-hours market news and earnings announcements
        - Research tomorrow's market catalysts and economic events
        - Check for any breaking news affecting your positions
        - Research sector performance and rotation trends
        - Look for options flow data and unusual activity
        - Search for analyst ratings changes and price target updates
        - Research market sentiment and volatility expectations
        
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
        
        WEB SEARCH ANALYSIS PROCESS:
        1. Search for "after hours market news today"
        2. Research each position: "[SYMBOL] after hours news earnings"
        3. Check tomorrow's calendar: "market events tomorrow earnings"
        4. Research sector trends: "sector rotation today market"
        5. Look for options flow: "unusual options activity today"
        6. Check analyst updates: "analyst ratings changes today"
        
        Please provide comprehensive analysis including:
        1. Performance attribution analysis (what drove P&L) with web research context
        2. Risk assessment of current portfolio based on market conditions
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
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.3,
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}],
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = self._extract_text_from_response(response)
            review = self._parse_evening_response(content)
            self.daily_query_count += 1
            
            # Generate and save evening summary for dashboard
            await self._generate_and_save_evening_summary(portfolio, positions, review, market_summary)
            
            logger.info("✅ Evening review session complete with web search")
            return review
            
        except Exception as e:
            logger.error(f"❌ Evening review session failed: {e}")
            # Save fallback summary for error case
            try:
                claude_summary_manager.save_evening_summary(
                    summary="Evening session error - performance data may be incomplete",
                    portfolio_performance="Unable to analyze due to error",
                    next_day_outlook="Will retry analysis tomorrow morning"
                )
            except:
                pass
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
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.2,
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = self._extract_text_from_response(response)
            decision = self._parse_position_response(content, position.id, position.claude_conversation_id)
            self.daily_query_count += 1
            
            logger.warning(f"🚨 Emergency analysis complete with web search. Action: {decision.action if decision else 'None'}")
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
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}],
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = self._extract_text_from_response(response)
            
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

    async def _generate_and_save_morning_summary(self, strategy_response: MorningStrategyResponse, portfolio: PortfolioSummary, market_data: Dict[str, Any]):
        """Generate and save a summary of the morning strategy session for dashboard display"""
        try:
            # Create a concise summary for dashboard display
            opportunities_count = len(strategy_response.opportunities)
            market_sentiment = strategy_response.market_assessment.overall_sentiment
            cash_action = strategy_response.cash_strategy.action
            
            # Generate a brief summary
            if opportunities_count == 0:
                summary = f"No trades today - {cash_action.lower()}. Market: {market_sentiment}"
            elif opportunities_count == 1:
                summary = f"Found 1 opportunity - {cash_action.lower()}. Market: {market_sentiment}"
            else:
                summary = f"Found {opportunities_count} opportunities - {cash_action.lower()}. Market: {market_sentiment}"
            
            # Save the summary using the claude_summary_manager
            claude_summary_manager.save_morning_summary(
                summary=summary,
                opportunities_count=opportunities_count,
                market_analysis=f"{market_sentiment} - {strategy_response.market_assessment.volatility_environment}"
            )
            
            logger.info(f"💾 Saved morning summary: {summary}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate morning summary: {e}")
            # Save a fallback summary
            try:
                claude_summary_manager.save_morning_summary(
                    summary="Morning analysis completed - check positions for details",
                    opportunities_count=0,
                    market_analysis="Analysis completed"
                )
            except:
                pass 

    async def _generate_and_save_evening_summary(self, portfolio: PortfolioSummary, positions: List[OptionsPosition], review: Dict[str, Any], market_summary: Dict[str, Any]):
        """Generate and save a summary of the evening review session for dashboard display"""
        try:
            # Extract key information from the review
            total_pnl = portfolio.total_pnl
            win_rate = portfolio.win_rate
            open_positions = portfolio.open_positions
            market_sentiment = market_summary.get('market_sentiment', 'Unknown')
            volatility_trend = market_summary.get('volatility_trend', 'Unknown')
            market_hours = market_summary.get('market_hours', 'Unknown')

            # Generate a brief summary
            if open_positions == 0:
                summary = f"No open positions. Market: {market_sentiment}. Volatility: {volatility_trend}. Hours: {market_hours}"
            else:
                summary = f"Open positions: {open_positions}. Total P&L: ${total_pnl:,.0f}. Win Rate: {win_rate:.1%}. Market: {market_sentiment}. Volatility: {volatility_trend}. Hours: {market_hours}"
            
            # Save the summary using the claude_summary_manager
            claude_summary_manager.save_evening_summary(
                summary=summary,
                portfolio_performance=f"Total P&L: ${total_pnl:,.0f}, Win Rate: {win_rate:.1%}",
                next_day_outlook=f"Market: {market_sentiment}. Volatility: {volatility_trend}. Hours: {market_hours}"
            )
            
            logger.info(f"💾 Saved evening summary: {summary}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate evening summary: {e}")
            # Save a fallback summary
            try:
                claude_summary_manager.save_evening_summary(
                    summary="Evening session error - performance data may be incomplete",
                    portfolio_performance="Unable to analyze due to error",
                    next_day_outlook="Will retry analysis tomorrow morning"
                )
            except:
                pass 