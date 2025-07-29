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
    
    async def morning_strategy_session(self, 
                                     portfolio: PortfolioSummary,
                                     market_data: Dict[str, Any],
                                     earnings_calendar: List[Dict],
                                     current_positions: List[OptionsPosition]) -> List[OptionsOpportunity]:
        """
        Morning Claude session for options strategy and stock selection
        """
        logger.info("🌅 Starting morning Claude strategy session")
        
        if self.daily_query_count >= settings.CLAUDE_MAX_DAILY_QUERIES:
            logger.warning("Daily Claude query limit reached")
            return []
        
        # Prepare context for Claude
        context = self._prepare_morning_context(portfolio, market_data, earnings_calendar, current_positions)
        
        prompt = f"""
        You are an expert options trader analyzing market conditions for today's trading opportunities.
        
        Current Portfolio Status:
        {context['portfolio']}
        
        Market Conditions:
        {context['market']}
        
        Upcoming Earnings (Next 2 weeks):
        {context['earnings']}
        
        Current Positions:
        {context['positions']}
        
        TASK: Identify 2-3 high-probability options opportunities for today with 2-4 week holding periods.
        
        CRITICAL: Consider portfolio Greeks limits:
        - Current portfolio delta: {portfolio.total_delta}
        - Current portfolio vega: {portfolio.total_vega}
        - Maximum recommended delta exposure: ±0.3
        - Maximum recommended vega: $500 per 1% IV move
        
        RESPONSE FORMAT: Return ONLY valid JSON array. No additional text, explanation, or markdown.
        
        Schema:
        [
          {{
            "symbol": "AAPL",
            "strategy_type": "long_call",
            "contracts": [
              {{
                "option_type": "call",
                "strike_price": 150.0,
                "expiration_date": "2024-02-16",
                "quantity": 1
              }}
            ],
            "rationale": "Strong technical setup with bullish divergence...",
            "confidence": 0.85,
            "risk_assessment": "Low risk due to defined max loss...",
            "target_return": 50.0,
            "max_risk": 500.0,
            "time_horizon": 21
          }}
        ]
        
        Analysis Focus:
        - Options with favorable IV rank vs historical volatility
        - Upcoming earnings or events that could drive volatility
        - Technical setups that suggest directional moves
        - Positions that complement existing portfolio
        """
        
        try:
            response = await self._query_claude(prompt, "morning_strategy")
            opportunities = self._parse_morning_response(response)
            self.daily_query_count += 1
            
            logger.info(f"✅ Morning session complete. Found {len(opportunities)} opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Morning strategy session failed: {e}")
            return []
    
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
        """Prepare context for morning session"""
        return {
            "portfolio": json.dumps({
                "total_value": portfolio.total_value,
                "cash_balance": portfolio.cash_balance,
                "open_positions": portfolio.open_positions,
                "total_delta": portfolio.total_delta,
                "total_vega": portfolio.total_vega
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
    
    def _parse_morning_response(self, response: str) -> List[OptionsOpportunity]:
        """Parse Claude's morning strategy response"""
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
            
            # Validate it's a list
            if not isinstance(data, list):
                logger.error(f"Expected array, got {type(data)}")
                return []
            
            # Convert to OptionsOpportunity objects
            opportunities = []
            for item in data:
                try:
                    opportunity = OptionsOpportunity(**item)
                    opportunities.append(opportunity)
                except Exception as e:
                    logger.error(f"Invalid opportunity format: {e}")
                    continue
            
            return opportunities
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response content: {response[:500]}...")
        except Exception as e:
            logger.error(f"Failed to parse morning response: {e}")
        
        return []
    
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