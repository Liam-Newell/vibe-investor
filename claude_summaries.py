#!/usr/bin/env python3
"""
Claude Session Summaries Manager
Stores and retrieves Claude's session summaries for dashboard display
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ClaudeSummaryManager:
    """Manages Claude session summaries for dashboard display"""
    
    def __init__(self, summary_file: str = "claude_summaries.json"):
        self.summary_file = Path(summary_file)
        self.ensure_summary_file_exists()
    
    def ensure_summary_file_exists(self):
        """Create the summary file if it doesn't exist"""
        if not self.summary_file.exists():
            initial_data = {
                "latest_summary": "🤖 Autonomous trading system ready - awaiting first Claude session",
                "last_updated": datetime.now().isoformat(),
                "session_history": []
            }
            self.save_summary_data(initial_data)
    
    def save_summary_data(self, data: Dict[str, Any]):
        """Save summary data to JSON file"""
        try:
            with open(self.summary_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save summary data: {e}")
    
    def load_summary_data(self) -> Dict[str, Any]:
        """Load summary data from JSON file"""
        try:
            with open(self.summary_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load summary data: {e}")
            return {
                "latest_summary": "🤖 System ready for Claude analysis",
                "last_updated": datetime.now().isoformat(),
                "session_history": []
            }
    
    def save_morning_summary(self, summary: str, opportunities_count: int, market_analysis: str):
        """Save a morning session summary"""
        try:
            data = self.load_summary_data()
            
            # Format the summary with date
            formatted_date = datetime.now().strftime("%B %d, %Y")
            full_summary = f"🌅 {summary} - {formatted_date}"
            
            # Update latest summary
            data["latest_summary"] = full_summary
            data["last_updated"] = datetime.now().isoformat()
            
            # Add to history
            session_record = {
                "type": "morning",
                "summary": full_summary,
                "timestamp": datetime.now().isoformat(),
                "opportunities_count": opportunities_count,
                "market_analysis": market_analysis
            }
            
            data["session_history"].append(session_record)
            
            # Keep only last 10 sessions
            if len(data["session_history"]) > 10:
                data["session_history"] = data["session_history"][-10:]
            
            self.save_summary_data(data)
            logger.info(f"💾 Saved morning summary: {full_summary}")
            
        except Exception as e:
            logger.error(f"Failed to save morning summary: {e}")
    
    def save_evening_summary(self, summary: str, portfolio_performance: str, next_day_outlook: str):
        """Save an evening session summary"""
        try:
            data = self.load_summary_data()
            
            # Format the summary with date
            formatted_date = datetime.now().strftime("%B %d, %Y")
            full_summary = f"🌆 {summary} - {formatted_date}"
            
            # Update latest summary
            data["latest_summary"] = full_summary
            data["last_updated"] = datetime.now().isoformat()
            
            # Add to history
            session_record = {
                "type": "evening",
                "summary": full_summary,
                "timestamp": datetime.now().isoformat(),
                "portfolio_performance": portfolio_performance,
                "next_day_outlook": next_day_outlook
            }
            
            data["session_history"].append(session_record)
            
            # Keep only last 10 sessions
            if len(data["session_history"]) > 10:
                data["session_history"] = data["session_history"][-10:]
            
            self.save_summary_data(data)
            logger.info(f"💾 Saved evening summary: {full_summary}")
            
        except Exception as e:
            logger.error(f"Failed to save evening summary: {e}")
    
    def get_latest_summary(self) -> str:
        """Get the latest Claude summary for dashboard display"""
        try:
            data = self.load_summary_data()
            return data.get("latest_summary", "🤖 System ready for Claude analysis")
        except Exception as e:
            logger.error(f"Failed to get latest summary: {e}")
            return "🤖 System ready for Claude analysis"
    
    def get_summary_with_metadata(self) -> Dict[str, Any]:
        """Get the latest summary with metadata"""
        try:
            data = self.load_summary_data()
            return {
                "summary": data.get("latest_summary", "🤖 System ready for Claude analysis"),
                "last_updated": data.get("last_updated", datetime.now().isoformat()),
                "session_count": len(data.get("session_history", []))
            }
        except Exception as e:
            logger.error(f"Failed to get summary with metadata: {e}")
            return {
                "summary": "🤖 System ready for Claude analysis",
                "last_updated": datetime.now().isoformat(),
                "session_count": 0
            }
    
    def get_session_history(self) -> list:
        """Get the history of Claude sessions"""
        try:
            data = self.load_summary_data()
            return data.get("session_history", [])
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []

# Global instance
claude_summary_manager = ClaudeSummaryManager() 