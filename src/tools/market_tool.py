"""
Market Data Tool for Daily Digest
Fetches stock market indexes and investment news
"""

from datetime import datetime
from typing import Dict, Any, List
import random

from utils.config import get_config
from utils.logging import get_logger
from utils.metrics import get_metrics


logger = get_logger()
metrics = get_metrics()


def get_market_data(indexes: List[str] = None) -> Dict[str, Any]:
    """
    Fetches current market data for major indexes.
    
    NOTE: This is a mock implementation. In production, replace with:
    - Alpha Vantage (https://www.alphavantage.co/)
    - Yahoo Finance API
    - Financial Modeling Prep API
    
    Args:
        indexes: List of index symbols (e.g., ["^GSPC", "^IXIC", "^DJI"])
                ^GSPC = S&P 500, ^IXIC = NASDAQ, ^DJI = DOW JONES
                If not provided, uses default indexes from config.
    
    Returns:
        Dictionary containing:
        - indexes: List of index data (name, symbol, value, change, change_percent)
        - market_summary: Brief market summary
        - timestamp: ISO format timestamp
        - source: Data source
        - error: Error message if failed
    
    Example:
        >>> market = get_market_data(["^GSPC", "^IXIC"])
        >>> print(market['indexes'][0]['value'])
        4500.25
    """
    config = get_config()
    
    # Use provided indexes or defaults
    if indexes is None:
        indexes = config.market_indexes
    
    logger.info("Fetching market data", indexes=indexes)
    metrics.start_timer("tool.get_market_data")
    
    try:
        if config.finance_api_key:
            logger.warning("Finance API key detected but not implemented yet - using mock data")
        
        # Mock data (replace with real API calls)
        result = {
            'indexes': _generate_mock_indexes(indexes),
            'market_summary': _generate_market_summary(),
            'timestamp': datetime.now().isoformat(),
            'source': 'Mock Market Data (replace with Alpha Vantage or Yahoo Finance)'
        }
        
        duration = metrics.stop_timer("tool.get_market_data", {"tool": "get_market_data", "type": "tool"})
        logger.info(
            "Market data fetched successfully",
            indexes=indexes,
            duration_ms=duration
        )
        
        return result
        
    except Exception as e:
        duration = metrics.stop_timer("tool.get_market_data", {"tool": "get_market_data", "type": "tool"})
        metrics.increment("tool.error", {"tool": "get_market_data"})
        
        logger.error(
            "Failed to fetch market data",
            exception=e,
            indexes=indexes,
            duration_ms=duration
        )
        
        return {
            'error': str(e),
            'indexes': [],
            'timestamp': datetime.now().isoformat(),
            'source': 'Market API (failed)'
        }


def _generate_mock_indexes(symbols: List[str]) -> List[Dict[str, Any]]:
    """Generate realistic mock market data"""
    
    index_names = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "^DJI": "DOW JONES"
    }
    
    base_values = {
        "^GSPC": 4500,
        "^IXIC": 14000,
        "^DJI": 35000
    }
    
    indexes = []
    for symbol in symbols:
        base_value = base_values.get(symbol, 1000)
        value = base_value + random.uniform(-50, 50)
        change = random.uniform(-100, 100)
        change_percent = (change / value) * 100
        
        indexes.append({
            'name': index_names.get(symbol, symbol),
            'symbol': symbol,
            'value': round(value, 2),
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'is_positive': change > 0
        })
    
    return indexes


def _generate_market_summary() -> str:
    """Generate a realistic market summary"""
    sentiments = [
        "Markets showed mixed performance today as investors digest economic data.",
        "Stocks climbed higher on positive earnings reports and economic optimism.",
        "Markets pulled back amid concerns about inflation and interest rates.",
        "Tech stocks led gains as the broader market advanced.",
        "Major indexes ended mostly flat in cautious trading."
    ]
    return random.choice(sentiments)


# ============================================================================
# Production Implementation with Alpha Vantage
# ============================================================================
"""
To implement with Alpha Vantage API:

import requests

def _fetch_real_market_data(symbols: List[str], api_key: str) -> List[Dict[str, Any]]:
    indexes = []
    
    for symbol in symbols:
        # Remove ^ prefix for API call
        api_symbol = symbol.replace('^', '')
        
        # Fetch quote data
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': api_symbol,
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Global Quote' in data:
            quote = data['Global Quote']
            indexes.append({
                'name': _get_index_name(symbol),
                'symbol': symbol,
                'value': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': float(quote.get('10. change percent', '0').replace('%', '')),
                'is_positive': float(quote.get('09. change', 0)) > 0
            })
    
    return indexes

def _get_index_name(symbol: str) -> str:
    names = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "^DJI": "DOW JONES"
    }
    return names.get(symbol, symbol)
"""
