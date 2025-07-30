"""
Configuration Management
Loads settings from environment variables
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Critical: Paper Trading Mode
    PAPER_TRADING_ONLY: bool = Field(True, description="Enable paper trading mode (NEVER set to False in production without testing)")
    
    # API Keys and External Services
    CLAUDE_API_KEY: str = Field(..., description="Anthropic Claude API key")
    CLAUDE_MODEL: str = Field("claude-3-sonnet-20240229", description="Claude model to use")
    
    # Broker Configuration
    BROKER_TYPE: str = Field("ibkr", description="Broker type: ibkr or questtrade")
    
    # Interactive Brokers
    IBKR_TWS_HOST: str = Field("127.0.0.1", description="TWS/Gateway host")
    IBKR_TWS_PORT: int = Field(7497, description="TWS/Gateway port (7497 for paper, 7496 for live)")
    IBKR_CLIENT_ID: int = Field(1, description="Client ID for IBKR connection")
    
    # Questtrade
    QUESTRADE_REFRESH_TOKEN: Optional[str] = Field(None, description="Questtrade refresh token")
    QUESTRADE_API_SERVER: Optional[str] = Field(None, description="Questtrade API server URL")
    
    # Market Data
    ALPHA_VANTAGE_API_KEY: Optional[str] = Field(None, description="Alpha Vantage API key")
    POLYGON_API_KEY: Optional[str] = Field(None, description="Polygon.io API key")
    
    # Database Configuration
    DATABASE_URL: str = Field("postgresql://trader:password@localhost/vibe_investor", description="Database connection URL")
    REDIS_URL: str = Field("redis://localhost:6379", description="Redis connection URL")
    DB_PASSWORD: str = Field("secure_password", description="Database password")
    REDIS_PASSWORD: str = Field("secure_password", description="Redis password")
    
    # Claude Configuration
    CLAUDE_MORNING_ENABLED: bool = Field(True, description="Enable morning Claude strategy session")
    CLAUDE_EVENING_ENABLED: bool = Field(True, description="Enable evening Claude review session")
    CLAUDE_MAX_DAILY_QUERIES: int = Field(10, description="Maximum Claude queries per day")
    CLAUDE_MORNING_TIME: str = Field("08:00", description="Morning session time (HH:MM)")
    CLAUDE_EVENING_TIME: str = Field("17:00", description="Evening session time (HH:MM)")
    
    # Trading Strategy Configuration
    MAX_SWING_POSITIONS: int = Field(6, description="Maximum concurrent options positions")
    TARGET_DAILY_RETURN: float = Field(0.002, description="Target daily return (0.2% = realistic)")
    ENABLE_TRADITIONAL_BENCHMARK: bool = Field(False, description="Enable traditional TA benchmark")
    ENABLE_OPTIONS_INCOME: bool = Field(True, description="Enable options income strategies")
    
    # Position Sizing
    DEFAULT_POSITION_SIZE_PCT: float = Field(2.0, description="Default position size as % of portfolio")
    MAX_POSITION_SIZE_PCT: float = Field(10.0, description="Maximum position size as % of portfolio")
    DEFAULT_STOP_LOSS_PCT: float = Field(50.0, description="Default stop-loss percentage for options")
    MAX_HOLDING_PERIOD_DAYS: int = Field(30, description="Maximum days to hold a position")
    
    # Options-Specific Configuration
    MIN_DAYS_TO_EXPIRATION: int = Field(7, description="Minimum days to expiration for new positions")
    MAX_DAYS_TO_EXPIRATION: int = Field(60, description="Maximum days to expiration for new positions")
    MIN_OPTION_VOLUME: int = Field(100, description="Minimum daily volume for options")
    MIN_OPTION_OPEN_INTEREST: int = Field(500, description="Minimum open interest for options")
    
    # Dynamic Confidence Thresholds (Research-Based)
    MIN_CONFIDENCE_LONG_PUTS: float = Field(0.78, description="Minimum confidence for long puts (high volatility risk)")
    MIN_CONFIDENCE_LONG_CALLS: float = Field(0.75, description="Minimum confidence for long calls (directional risk)")
    MIN_CONFIDENCE_CREDIT_SPREADS: float = Field(0.68, description="Minimum confidence for credit spreads (defined risk)")
    MIN_CONFIDENCE_IRON_CONDORS: float = Field(0.65, description="Minimum confidence for iron condors (market neutral)")
    MIN_CONFIDENCE_PUT_SPREADS: float = Field(0.70, description="Minimum confidence for put spreads")
    
    # Performance-Based Confidence Adjustments
    CONFIDENCE_BOOST_AFTER_LOSSES: float = Field(0.10, description="Increase confidence threshold after losses")
    CONFIDENCE_REDUCTION_AFTER_WINS: float = Field(0.05, description="Decrease confidence threshold after wins")
    MIN_CONFIDENCE_FLOOR: float = Field(0.60, description="Absolute minimum confidence for any trade")
    MAX_CONFIDENCE_CEILING: float = Field(0.95, description="Maximum confidence threshold")
    
    # Auto-Execution Settings
    AUTO_EXECUTE_TRADES: bool = Field(True, description="Enable automatic trade execution")
    MAX_DAILY_POSITIONS: int = Field(3, description="Maximum new positions per day")
    MIN_CASH_RESERVE_FOR_TRADES: float = Field(10000.0, description="Minimum cash reserve before auto-trading")
    
    # Greeks Limits
    MAX_PORTFOLIO_DELTA: float = Field(0.3, description="Maximum portfolio delta exposure")
    MAX_PORTFOLIO_VEGA: float = Field(500.0, description="Maximum portfolio vega ($500 per 1% IV)")
    MAX_PORTFOLIO_THETA: float = Field(-100.0, description="Maximum negative theta (daily decay)")
    
    # Technical Indicators Configuration
    RSI_PERIOD: int = Field(14, description="RSI calculation period")
    MACD_FAST: int = Field(12, description="MACD fast EMA")
    MACD_SLOW: int = Field(26, description="MACD slow EMA")
    MACD_SIGNAL: int = Field(9, description="MACD signal line EMA")
    SMA_SHORT: int = Field(20, description="Short-term moving average")
    SMA_LONG: int = Field(50, description="Long-term moving average")
    
    # Email Notifications
    EMAIL_ENABLED: bool = Field(False, description="Enable email notifications")
    SMTP_SERVER: str = Field("smtp.gmail.com", description="SMTP server")
    SMTP_PORT: int = Field(587, description="SMTP port")
    SMTP_USER: Optional[str] = Field(None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(None, description="SMTP password (use app password)")
    ALERT_EMAIL: Optional[str] = Field(None, description="Email address for alerts")
    
    # Email Frequency
    DAILY_SUMMARY_ENABLED: bool = Field(True, description="Send daily summary emails")
    TRADE_CONFIRMATION_ENABLED: bool = Field(True, description="Send trade confirmation emails")
    ERROR_ALERT_ENABLED: bool = Field(True, description="Send error alert emails")
    WEEKLY_REPORT_ENABLED: bool = Field(True, description="Send weekly performance reports")
    
    # Dashboard Configuration  
    DASHBOARD_HOST: str = Field("0.0.0.0", description="Dashboard host")
    DASHBOARD_PORT: int = Field(8080, description="Dashboard web server port")
    PORT: int = Field(8000, description="Main application server port")
    DEBUG: bool = Field(False, description="Enable debug mode")
    
    # Security (Optional)
    DASHBOARD_AUTH_ENABLED: bool = Field(False, description="Enable dashboard authentication")
    DASHBOARD_USERNAME: str = Field("admin", description="Dashboard username")
    DASHBOARD_PASSWORD: str = Field("secure_password", description="Dashboard password")
    
    # Risk Management
    MAX_DAILY_LOSS_PCT: float = Field(5.0, description="Maximum daily loss percentage")
    MAX_DRAWDOWN_PCT: float = Field(15.0, description="Maximum portfolio drawdown percentage")
    CIRCUIT_BREAKER_ENABLED: bool = Field(True, description="Enable circuit breaker protection")
    EMERGENCY_STOP_LOSS_PCT: float = Field(20.0, description="Emergency stop-loss percentage")
    
    # Portfolio Limits
    MAX_SECTOR_CONCENTRATION_PCT: float = Field(40.0, description="Maximum sector concentration")
    MAX_SINGLE_POSITION_PCT: float = Field(15.0, description="Maximum single position percentage")
    MIN_CASH_RESERVE_PCT: float = Field(20.0, description="Minimum cash reserve percentage")
    
    # Logging & Monitoring
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_RETENTION_DAYS: int = Field(90, description="Log file retention period")
    ENABLE_PERFORMANCE_METRICS: bool = Field(True, description="Enable performance metrics collection")
    ENABLE_HEALTH_CHECKS: bool = Field(True, description="Enable system health checks")
    
    # Backup Configuration
    BACKUP_ENABLED: bool = Field(True, description="Enable automated backups")
    BACKUP_SCHEDULE: str = Field("0 2 * * *", description="Backup cron schedule")
    BACKUP_RETENTION_DAYS: int = Field(30, description="Backup retention period")
    BACKUP_ENCRYPTION_ENABLED: bool = Field(False, description="Enable backup encryption")
    BACKUP_GPG_KEY_ID: Optional[str] = Field(None, description="GPG key ID for backup encryption")
    
    # Optional Webhooks
    DISCORD_WEBHOOK_URL: Optional[str] = Field(None, description="Discord webhook URL")
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(None, description="Telegram bot token")
    TELEGRAM_CHAT_ID: Optional[str] = Field(None, description="Telegram chat ID")
    
    # Development Settings
    DEVELOPMENT_MODE: bool = Field(False, description="Enable development features")
    ENABLE_API_DOCS: bool = Field(True, description="Enable FastAPI auto-generated docs")
    
    # Timezone & Market Settings
    TIMEZONE: str = Field("America/New_York", description="System timezone")
    MARKET_TIMEZONE: str = Field("America/New_York", description="Market timezone")
    TRADING_DAYS: str = Field("Monday,Tuesday,Wednesday,Thursday,Friday", description="Trading days")
    MARKET_OPEN_TIME: str = Field("09:30", description="Market open time")
    MARKET_CLOSE_TIME: str = Field("16:00", description="Market close time")
    
    # Advanced Settings
    DATABASE_POOL_SIZE: int = Field(10, description="Database connection pool size")
    REDIS_MAX_CONNECTIONS: int = Field(20, description="Redis max connections")
    API_TIMEOUT_SECONDS: int = Field(30, description="API request timeout")
    MAX_RETRY_ATTEMPTS: int = Field(3, description="Maximum retry attempts for API calls")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(60, description="Rate limit for API requests")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra environment variables
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_critical_settings()
    
    def _validate_critical_settings(self):
        """Validate critical settings that could cause issues"""
        
        # Ensure paper trading is enabled for safety
        if not self.PAPER_TRADING_ONLY:
            import warnings
            warnings.warn(
                "⚠️  PAPER_TRADING_ONLY is disabled! This will trade with real money. "
                "Only disable after extensive paper trading validation.",
                UserWarning
            )
        
        # Validate position sizing
        if self.DEFAULT_POSITION_SIZE_PCT > self.MAX_POSITION_SIZE_PCT:
            raise ValueError("Default position size cannot exceed maximum position size")
        
        if self.MAX_POSITION_SIZE_PCT > 25.0:
            raise ValueError("Maximum position size should not exceed 25% for safety")
        
        # Validate Greeks limits
        if self.MAX_PORTFOLIO_DELTA > 1.0:
            raise ValueError("Portfolio delta exposure should not exceed 1.0")
        
        # Validate Claude settings
        if self.CLAUDE_MAX_DAILY_QUERIES > 50:
            import warnings
            warnings.warn("High Claude query limit may result in expensive API costs", UserWarning)
        
        # Validate risk settings
        if self.MAX_DAILY_LOSS_PCT > 10.0:
            raise ValueError("Maximum daily loss should not exceed 10% for safety")
    
    @property
    def trading_days_list(self) -> List[str]:
        """Get trading days as a list"""
        return [day.strip() for day in self.TRADING_DAYS.split(",")]
    
    @property
    def is_production_ready(self) -> bool:
        """Check if configuration is ready for production"""
        required_fields = [
            self.CLAUDE_API_KEY,
            self.DATABASE_URL,
            self.REDIS_URL
        ]
        
        return all(field for field in required_fields)
    
    def get_broker_config(self) -> dict:
        """Get broker-specific configuration"""
        if self.BROKER_TYPE.lower() == "ibkr":
            return {
                "type": "ibkr",
                "host": self.IBKR_TWS_HOST,
                "port": self.IBKR_TWS_PORT,
                "client_id": self.IBKR_CLIENT_ID,
                "paper_trading": self.PAPER_TRADING_ONLY
            }
        elif self.BROKER_TYPE.lower() == "questtrade":
            return {
                "type": "questtrade",
                "refresh_token": self.QUESTRADE_REFRESH_TOKEN,
                "api_server": self.QUESTRADE_API_SERVER,
                "paper_trading": self.PAPER_TRADING_ONLY
            }
        else:
            raise ValueError(f"Unsupported broker type: {self.BROKER_TYPE}")
    
    def get_email_config(self) -> dict:
        """Get email configuration"""
        return {
            "enabled": self.EMAIL_ENABLED,
            "smtp_server": self.SMTP_SERVER,
            "smtp_port": self.SMTP_PORT,
            "smtp_user": self.SMTP_USER,
            "smtp_password": self.SMTP_PASSWORD,
            "alert_email": self.ALERT_EMAIL,
            "daily_summary": self.DAILY_SUMMARY_ENABLED,
            "trade_confirmations": self.TRADE_CONFIRMATION_ENABLED,
            "error_alerts": self.ERROR_ALERT_ENABLED,
            "weekly_reports": self.WEEKLY_REPORT_ENABLED
        }

# Global settings instance
settings = Settings()

# Validate configuration on import
if not settings.is_production_ready:
    import warnings
    warnings.warn(
        "Configuration is not production ready. Please check required environment variables.",
        UserWarning
    ) 