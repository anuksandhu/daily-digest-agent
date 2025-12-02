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
    
    Uses News API if key is available, otherwise falls back to mock data.
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
        # Use real News API if key is available
        if config.news_api_key:
            logger.info("Using News API for real data")
            result = _fetch_real_news(config.news_api_key, topics, limit)
        else:
            logger.warning("No News API key - using mock data")
            result = {
                'articles': _generate_mock_articles(topics, limit),
                'timestamp': datetime.now().isoformat(),
                'source': 'Mock News Data (add NEWS_API_KEY for real data)'
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
        
        # Return error with fallback to mock data
        return {
            'articles': _generate_mock_articles(topics, limit),
            'timestamp': datetime.now().isoformat(),
            'source': 'Mock News Data (API failed)',
            'error': str(e)
        }


def _fetch_real_news(api_key: str, topics: List[str], limit: int) -> Dict[str, Any]:
    """
    Fetch real news from News API
    
    Args:
        api_key: News API key
        topics: List of search topics
        limit: Number of articles to return
    
    Returns:
        Dictionary with articles and metadata
    """
    import requests
    
    # Build query from topics
    query = " OR ".join(topics)
    
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
    
    articles = []
    for article in data.get('articles', [])[:limit]:
        # Extract clean summary (description or first 200 chars of content)
        summary = article.get('description') or ''
        if not summary and article.get('content'):
            summary = article.get('content', '')[:200].strip()
        
        articles.append({
            'title': article.get('title', 'No title'),
            'summary': summary,
            'source': article.get('source', {}).get('name', 'Unknown'),
            'url': article.get('url', '#'),
            'published_at': article.get('publishedAt', datetime.now().isoformat()),
            'category': 'technology'
        })
    
    return {
        'articles': articles,
        'timestamp': datetime.now().isoformat(),
        'source': 'News API'
    }


def _generate_mock_articles(topics: List[str], limit: int) -> List[Dict[str, Any]]:
    """
    Generate mock news articles for testing
    
    Args:
        topics: List of topics (used for variety)
        limit: Number of articles to generate
    
    Returns:
        List of mock article dictionaries
    """
    sources = ["TechCrunch", "The Verge", "Ars Technica", "VentureBeat", "Wired"]
    
    mock_titles = [
        "Major AI breakthrough announced in language understanding",
        "New machine learning model achieves record performance",
        "Tech giant releases open-source AI framework",
        "Artificial intelligence transforming healthcare industry",
        "Breakthrough in neural network efficiency",
        "Quantum computing reaches new milestone",
        "AI startup raises significant funding round",
        "Research reveals advances in computer vision"
    ]
    
    articles = []
    for i in range(min(limit, len(mock_titles))):
        # Random recent date
        hours_ago = random.randint(6, 72)
        pub_date = datetime.now() - timedelta(hours=hours_ago)
        
        # Pick topic for this article
        topic = random.choice(topics) if topics else "technology"
        
        articles.append({
            'title': mock_titles[i],
            'summary': f"This article discusses recent developments in {topic}. Experts say this could have significant implications for the industry.",
            'source': random.choice(sources),
            'url': f"https://example.com/article-{i+1}",
            'published_at': pub_date.isoformat(),
            'category': 'technology'
        })
    
    return articles
