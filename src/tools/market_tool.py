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
    
    Uses Alpha Vantage API if key is available, otherwise falls back to mock data.
    Get API key from: https://www.alphavantage.co/support/#api-key
    
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
        # Use real Alpha Vantage API if key is available
        if config.finance_api_key:
            logger.info("Using Alpha Vantage API for real data")
            result = _fetch_real_market_data(config.finance_api_key, indexes)
        else:
            logger.warning("No Finance API key - using mock data")
            result = {
                'indexes': _generate_mock_indexes(indexes),
                'market_summary': _generate_market_summary(),
                'timestamp': datetime.now().isoformat(),
                'source': 'Mock Market Data (add FINANCE_API_KEY for real data)'
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
        
        # Return mock data on error
        return {
            'indexes': _generate_mock_indexes(indexes),
            'market_summary': 'Market data unavailable',
            'timestamp': datetime.now().isoformat(),
            'source': 'Mock Market Data (API failed)',
            'error': str(e)
        }


def _fetch_real_market_data(api_key: str, symbols: List[str]) -> Dict[str, Any]:
    """
    Fetch real market data from Alpha Vantage API
    
    Args:
        api_key: Alpha Vantage API key
        symbols: List of index symbols (e.g., ["^GSPC", "^IXIC", "^DJI"])
    
    Returns:
        Dictionary with indexes and market summary
    """
    import requests
    
    indexes = []
    
    # Symbol mapping - Alpha Vantage uses ETF proxies for indexes
    symbol_map = {
        '^GSPC': ('S&P 500', 'SPY'),      # SPDR S&P 500 ETF
        '^IXIC': ('NASDAQ', 'QQQ'),       # Invesco QQQ Trust
        '^DJI': ('DOW JONES', 'DIA')      # SPDR Dow Jones Industrial Average ETF
    }
    
    for symbol in symbols:
        name, ticker = symbol_map.get(symbol, (symbol, symbol.replace('^', '')))
        
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker,
            'apikey': api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            quote = data.get('Global Quote', {})
            
            if quote:
                price = float(quote.get('05. price', 0))
                change = float(quote.get('09. change', 0))
                change_pct = float(quote.get('10. change percent', '0').replace('%', ''))
                
                indexes.append({
                    'name': name,
                    'symbol': symbol,
                    'value': round(price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_pct, 2),
                    'is_positive': change > 0
                })
            else:
                logger.warning(f"No data returned for {symbol}")
                
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}")
            continue
    
    # If no data was fetched (API error/quota), fall back to mock
    if not indexes:
        logger.warning("No market data retrieved, using mock data")
        return {
            'indexes': _generate_mock_indexes(symbols),
            'market_summary': 'Market data unavailable (API quota exceeded)',
            'timestamp': datetime.now().isoformat(),
            'source': 'Mock Market Data (API quota exceeded)'
        }
    
    # Generate summary based on market performance
    positive_count = sum(1 for idx in indexes if idx.get('is_positive', False))
    total = len(indexes)
    
    if positive_count == total:
        summary = "Markets rallied across all major indexes on positive sentiment."
    elif positive_count >= total * 0.66:
        summary = "Markets mostly higher with broad-based gains."
    elif positive_count >= total * 0.33:
        summary = "Mixed trading session with varied performance across indexes."
    else:
        summary = "Markets declined on concerns about economic outlook."
    
    return {
        'indexes': indexes,
        'market_summary': summary,
        'timestamp': datetime.now().isoformat(),
        'source': 'Alpha Vantage API'
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