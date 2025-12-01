"""
Tech News Tool for Daily Digest
Fetches recent technology and AI news articles
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

from utils.config import get_config
from utils.logging import get_logger
from utils.metrics import get_metrics


logger = get_logger()
metrics = get_metrics()


def get_tech_news(topics: List[str] = None, limit: int = 5) -> Dict[str, Any]:
    """
    Fetches recent technology news articles.
    
    NOTE: This is a mock implementation. In production, replace with News API.
    Get API key from: https://newsapi.org/
    
    Args:
        topics: Keywords for filtering (e.g., ["AI", "machine learning"])
                If not provided, uses default topics from config.
        limit: Number of articles to return (default: 5)
    
    Returns:
        Dictionary containing:
        - articles: List of articles (title, summary, source, url, published_at)
        - timestamp: ISO format timestamp
        - source: Data source
        - error: Error message if failed
    
    Example:
        >>> news = get_tech_news(["AI", "ChatGPT"], limit=3)
        >>> print(news['articles'][0]['title'])
    """
    config = get_config()
    
    # Use provided topics or defaults
    if topics is None:
        topics = config.tech_topics
    
    logger.info("Fetching tech news", topics=topics, limit=limit)
    metrics.start_timer("tool.get_tech_news")
    
    try:
        if config.news_api_key:
            logger.warning("News API key detected but not implemented yet - using mock data")
        
        # Mock data (replace with real News API calls)
        result = {
            'articles': _generate_mock_articles(topics, limit),
            'timestamp': datetime.now().isoformat(),
            'source': 'Mock News Data (replace with News API)'
        }
        
        duration = metrics.stop_timer("tool.get_tech_news", {"tool": "get_tech_news", "type": "tool"})
        logger.info(
            "Tech news fetched successfully",
            topics=topics,
            article_count=len(result['articles']),
            duration_ms=duration
        )
        
        return result
        
    except Exception as e:
        duration = metrics.stop_timer("tool.get_tech_news", {"tool": "get_tech_news", "type": "tool"})
        metrics.increment("tool.error", {"tool": "get_tech_news"})
        
        logger.error(
            "Failed to fetch tech news",
            exception=e,
            topics=topics,
            duration_ms=duration
        )
        
        return {
            'error': str(e),
            'articles': [],
            'timestamp': datetime.now().isoformat(),
            'source': 'News API (failed)'
        }


def _generate_mock_articles(topics: List[str], limit: int) -> List[Dict[str, Any]]:
    """Generate realistic mock news articles"""
    
    sources = ["TechCrunch", "The Verge", "Ars Technica", "Wired", "VentureBeat"]
    
    sample_titles = [
        "Major AI breakthrough announced in language understanding",
        "New machine learning model achieves record performance",
        "Tech giant releases open-source AI framework",
        "Artificial intelligence transforming healthcare industry",
        "Breakthrough in neural network efficiency",
        "AI safety research sees significant progress",
        "Machine learning algorithm predicts market trends",
        "New AI chip promises 10x performance boost",
        "Researchers develop explainable AI system",
        "AI-powered tool revolutionizes software development"
    ]
    
    articles = []
    for i in range(min(limit, len(sample_titles))):
        days_ago = random.randint(0, 2)
        pub_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        articles.append({
            'title': sample_titles[i],
            'summary': f"This article discusses recent developments in {random.choice(topics)}. "
                      f"Experts say this could have significant implications for the industry.",
            'source': random.choice(sources),
            'url': f"https://example.com/article-{i+1}",
            'published_at': pub_date.isoformat(),
            'category': 'technology'
        })
    
    return articles


# ============================================================================
# Production Implementation with News API
# ============================================================================
"""
To implement with real News API:

import requests

def _fetch_real_tech_news(topics: List[str], limit: int, api_key: str) -> List[Dict[str, Any]]:
    # Build query
    query = " OR ".join(topics)
    
    # Call News API
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': query,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': limit,
        'apiKey': api_key
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    # Parse articles
    articles = []
    for article in data.get('articles', []):
        articles.append({
            'title': article['title'],
            'summary': article['description'] or article['content'][:200],
            'source': article['source']['name'],
            'url': article['url'],
            'published_at': article['publishedAt'],
            'category': 'technology'
        })
    
    return articles
"""
