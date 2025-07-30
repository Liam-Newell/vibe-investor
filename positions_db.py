#!/usr/bin/env python3
"""
Simple Position Database
Tracks real trading positions with persistence
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Trading position data structure"""
    id: str
    symbol: str
    strategy: str
    entry_cost: float
    entry_date: str
    contracts_data: str  # JSON string of contract details
    profit_target: float
    max_loss: float
    status: str = "OPEN"  # OPEN, CLOSED
    current_value: float = 0.0
    unrealized_pnl: float = 0.0
    close_date: Optional[str] = None
    close_reason: Optional[str] = None

class PositionDatabase:
    """Simple SQLite database for tracking positions"""
    
    def __init__(self, db_path: str = "positions.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create positions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    entry_cost REAL NOT NULL,
                    entry_date TEXT NOT NULL,
                    contracts_data TEXT NOT NULL,
                    profit_target REAL NOT NULL,
                    max_loss REAL NOT NULL,
                    status TEXT DEFAULT 'OPEN',
                    current_value REAL DEFAULT 0.0,
                    unrealized_pnl REAL DEFAULT 0.0,
                    close_date TEXT,
                    close_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create portfolio summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_summary (
                    id INTEGER PRIMARY KEY,
                    total_value REAL DEFAULT 100000.0,
                    cash_balance REAL DEFAULT 100000.0,
                    total_pnl REAL DEFAULT 0.0,
                    open_positions INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0.0,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    current_streak INTEGER DEFAULT 0,
                    max_positions INTEGER DEFAULT 6,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default portfolio if empty
            cursor.execute('SELECT COUNT(*) FROM portfolio_summary')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO portfolio_summary 
                    (total_value, cash_balance, total_pnl, open_positions, win_rate, total_trades, winning_trades, current_streak)
                    VALUES (100000.0, 100000.0, 0.0, 0, 0.0, 0, 0, 0)
                ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Position database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize position database: {e}")
            raise
    
    def add_position(self, position: Position) -> bool:
        """Add a new position to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert position
            cursor.execute('''
                INSERT INTO positions 
                (id, symbol, strategy, entry_cost, entry_date, contracts_data, profit_target, max_loss, status, current_value, unrealized_pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position.id, position.symbol, position.strategy, position.entry_cost,
                position.entry_date, position.contracts_data, position.profit_target,
                position.max_loss, position.status, position.current_value, position.unrealized_pnl
            ))
            
            # Update portfolio summary
            cursor.execute('UPDATE portfolio_summary SET open_positions = open_positions + 1, updated_at = CURRENT_TIMESTAMP')
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Added position: {position.symbol} {position.strategy}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add position: {e}")
            return False
    
    def get_all_positions(self, status: str = "OPEN") -> List[Position]:
        """Get all positions with specified status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM positions WHERE status = ? ORDER BY entry_date DESC', (status,))
            rows = cursor.fetchall()
            
            positions = []
            for row in rows:
                position = Position(
                    id=row[0], symbol=row[1], strategy=row[2], entry_cost=row[3],
                    entry_date=row[4], contracts_data=row[5], profit_target=row[6],
                    max_loss=row[7], status=row[8], current_value=row[9],
                    unrealized_pnl=row[10], close_date=row[11], close_reason=row[12]
                )
                positions.append(position)
            
            conn.close()
            return positions
            
        except Exception as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return []
    
    def update_position_value(self, position_id: str, current_value: float, unrealized_pnl: float) -> bool:
        """Update position's current value and P&L"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE positions 
                SET current_value = ?, unrealized_pnl = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (current_value, unrealized_pnl, position_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update position value: {e}")
            return False
    
    def close_position(self, position_id: str, close_reason: str = "Manual") -> bool:
        """Close a position"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get position to update portfolio
            cursor.execute('SELECT unrealized_pnl FROM positions WHERE id = ?', (position_id,))
            result = cursor.fetchone()
            if not result:
                return False
            
            pnl = result[0]
            
            # Close position
            cursor.execute('''
                UPDATE positions 
                SET status = 'CLOSED', close_date = ?, close_reason = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (datetime.now().isoformat(), close_reason, position_id))
            
            # Update portfolio summary
            cursor.execute('''
                UPDATE portfolio_summary 
                SET open_positions = open_positions - 1,
                    total_pnl = total_pnl + ?,
                    total_trades = total_trades + 1,
                    winning_trades = winning_trades + ?,
                    updated_at = CURRENT_TIMESTAMP
            ''', (pnl, 1 if pnl > 0 else 0))
            
            # Recalculate win rate
            cursor.execute('SELECT total_trades, winning_trades FROM portfolio_summary')
            trades_data = cursor.fetchone()
            if trades_data and trades_data[0] > 0:
                win_rate = trades_data[1] / trades_data[0]
                cursor.execute('UPDATE portfolio_summary SET win_rate = ?', (win_rate,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Closed position: {position_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to close position: {e}")
            return False
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM portfolio_summary ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            
            if not row:
                # Return default portfolio
                return {
                    "total_value": 100000.0,
                    "cash_balance": 100000.0,
                    "total_pnl": 0.0,
                    "open_positions": 0,
                    "win_rate": 0.0,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "current_streak": 0,
                    "max_positions": 6
                }
            
            # Calculate current portfolio value
            cursor.execute('SELECT SUM(current_value) FROM positions WHERE status = "OPEN"')
            positions_value = cursor.fetchone()[0] or 0.0
            
            # Calculate total unrealized PnL
            cursor.execute('SELECT SUM(unrealized_pnl) FROM positions WHERE status = "OPEN"')
            unrealized_pnl = cursor.fetchone()[0] or 0.0
            
            portfolio = {
                "total_value": row[1] + unrealized_pnl,  # base value + unrealized PnL
                "cash_balance": row[2],
                "total_pnl": row[3] + unrealized_pnl,  # realized + unrealized
                "open_positions": row[4],
                "win_rate": row[5],
                "total_trades": row[6],
                "winning_trades": row[7],
                "current_streak": row[8],
                "max_positions": row[9],
                "unrealized_pnl": unrealized_pnl,
                "positions_value": positions_value
            }
            
            conn.close()
            return portfolio
            
        except Exception as e:
            logger.error(f"❌ Failed to get portfolio summary: {e}")
            return {
                "total_value": 100000.0,
                "cash_balance": 100000.0,
                "total_pnl": 0.0,
                "open_positions": 0,
                "win_rate": 0.0,
                "current_streak": 0,
                "max_positions": 6
            }
    
    def get_held_symbols(self) -> List[str]:
        """Get list of symbols for open positions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT symbol FROM positions WHERE status = "OPEN"')
            symbols = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return symbols
            
        except Exception as e:
            logger.error(f"❌ Failed to get held symbols: {e}")
            return []

# Global database instance
db = PositionDatabase()

def add_sample_position():
    """Add a sample position for testing"""
    sample_position = Position(
        id=f"pos_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        symbol="AAPL",
        strategy="Long Call",
        entry_cost=2500.0,
        entry_date=datetime.now().isoformat(),
        contracts_data=json.dumps({"strike": 230, "expiry": "2025-08-15", "quantity": 1}),
        profit_target=3000.0,
        max_loss=2000.0
    )
    return db.add_position(sample_position)

if __name__ == "__main__":
    # Test the database
    print("🧪 Testing Position Database...")
    
    # Get current state
    portfolio = db.get_portfolio_summary()
    positions = db.get_all_positions()
    
    print(f"📊 Portfolio: ${portfolio['total_value']:,.0f} value, {portfolio['open_positions']} positions")
    print(f"📋 Current positions: {len(positions)}")
    
    if len(positions) == 0:
        print("💡 No positions found. Would you like to add a sample? (y/n)")
        # For demo, we'll just show the structure
        print("📝 Database structure ready for real positions!")
    
    print("✅ Database test complete!") 