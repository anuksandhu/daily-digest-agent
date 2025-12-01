"""
Configuration Management for Daily Digest
Centralizes all configuration settings and environment variables
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Application configuration"""
    
    # ========================================================================
    # API Keys (Required)
    # ========================================================================
    google_api_key: str
    openweather_api_key: str
    
    # ========================================================================
    # API Keys (Optional - will use mock data if not provided)
    # ========================================================================
    brave_api_key: Optional[str] = None
    sports_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    finance_api_key: Optional[str] = None
    
    # ========================================================================
    # Application Settings
    # ========================================================================
    default_location: str = "San Jose,US"
    log_level: str = "INFO"
    enable_tracing: bool = True
    
    # ========================================================================
    # Model Configuration
    # ========================================================================
    model_name: str = "gemini-2.5-flash-lite"
    max_retries: int = 5
    retry_exp_base: int = 7
    initial_retry_delay: int = 1
    
    # ========================================================================
    # Content Configuration
    # ========================================================================
    sports_teams: dict = None
    tech_topics: list = None
    market_indexes: list = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.sports_teams is None:
            self.sports_teams = {
                "nfl": "49ers",
                "nhl": "Sharks", 
                "nba": "Warriors"
            }
        
        if self.tech_topics is None:
            self.tech_topics = ["AI", "machine learning", "artificial intelligence"]
        
        if self.market_indexes is None:
            self.market_indexes = ["^GSPC", "^IXIC", "^DJI"]  # S&P 500, NASDAQ, DOW
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables"""
        
        # Required keys
        google_api_key = os.getenv("GOOGLE_API_KEY")
        openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        
        if not google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment. "
                "Please set it in .env file or environment variables."
            )
        
        if not openweather_api_key:
            raise ValueError(
                "OPENWEATHER_API_KEY not found in environment. "
                "Please set it in .env file or environment variables."
            )
        
        # Optional keys
        brave_api_key = os.getenv("BRAVE_API_KEY")
        sports_api_key = os.getenv("SPORTS_API_KEY")
        news_api_key = os.getenv("NEWS_API_KEY")
        finance_api_key = os.getenv("FINANCE_API_KEY")
        
        # Settings
        default_location = os.getenv("DEFAULT_LOCATION", "San Jose,US")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        enable_tracing = os.getenv("ENABLE_TRACING", "true").lower() == "true"
        
        return cls(
            google_api_key=google_api_key,
            openweather_api_key=openweather_api_key,
            brave_api_key=brave_api_key,
            sports_api_key=sports_api_key,
            news_api_key=news_api_key,
            finance_api_key=finance_api_key,
            default_location=default_location,
            log_level=log_level,
            enable_tracing=enable_tracing
        )


# Global configuration instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global configuration instance"""
    global config
    if config is None:
        config = Config.from_env()
    return config
