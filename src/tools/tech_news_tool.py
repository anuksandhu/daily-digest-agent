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
    Fetches recent technology news articles from premium tech sources via RSS feeds.

    Uses RSS feeds from TechCrunch, The Verge, Ars Technica, Wired, 
    MIT Technology Review, and VentureBeat. No API key required.

    Args:
        topics: Keywords for filtering (e.g., ["AI", "machine learning"])
                Articles are filtered to match at least one topic.
                If not provided, uses default topics from config.
        limit: Number of articles to return (default: 5)

    Returns:
        Dictionary containing:
        - articles: List of articles (title, summary, source, url, published_at)
        - timestamp: ISO format timestamp
        - source: Data source (RSS Feeds)
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
    
    def get_tech_news(topics: List[str] = None, limit: int = 5) -> Dict[str, Any]:
    config = get_config()
    
    if topics is None:
        topics = config.tech_topics
    
    logger.info("Fetching tech news", topics=topics, limit=limit)
    metrics.start_timer("tool.get_tech_news")
    
    try:
        # Always use RSS feeds (free, reliable, premium sources)
        logger.info("Using RSS feeds for real data")
        result = _fetch_real_news(None, topics, limit)  # api_key not needed
        
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
    Fetch real news from RSS feeds of premium tech sources
    
    Args:
        api_key: Not used for RSS (kept for compatibility)
        topics: Used for filtering articles
        limit: Number of articles to return
    
    Returns:
        Dictionary with articles and metadata
    """
    import feedparser
    from datetime import datetime, timedelta
    
    # Premium tech news RSS feeds
    rss_feeds = {
        'TechCrunch': 'https://techcrunch.com/feed/',
        'The Verge': 'https://www.theverge.com/rss/index.xml',
        'Ars Technica': 'https://feeds.arstechnica.com/arstechnica/index',
        'Wired': 'https://www.wired.com/feed/rss',
        'MIT Technology Review': 'https://www.technologyreview.com/feed/',
        'VentureBeat': 'https://venturebeat.com/feed/'
    }
    
    articles = []
    topics_lower = [t.lower() for t in topics]
    
    for source_name, feed_url in rss_feeds.items():
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:10]:  # Check first 10 from each source
                # Check if article is relevant to topics
                title = entry.get('title', '')
                summary = entry.get('summary', entry.get('description', ''))
                
                # Simple topic matching
                text_to_check = (title + ' ' + summary).lower()
                is_relevant = any(topic in text_to_check for topic in topics_lower)
                
                if not is_relevant:
                    continue
                
                # Get publish date
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if published:
                    pub_date = datetime(*published[:6]).isoformat() + 'Z'
                else:
                    pub_date = datetime.now().isoformat() + 'Z'
                
                articles.append({
                    'title': title,
                    'summary': summary[:200] if summary else '',
                    'source': source_name,
                    'url': entry.get('link', '#'),
                    'published_at': pub_date,
                    'category': 'technology'
                })
                
                if len(articles) >= limit:
                    break
            
            if len(articles) >= limit:
                break
                
        except Exception as e:
            logger.warning(f"Failed to fetch RSS from {source_name}: {e}")
            continue
    
    return {
        'articles': articles,
        'timestamp': datetime.now().isoformat(),
        'source': 'RSS Feeds (TechCrunch, The Verge, Ars Technica, Wired, MIT Tech Review, VentureBeat)'
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
