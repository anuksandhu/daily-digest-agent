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
    
    # Premium tech news RSS feeds - ORDERED for diversity
    # We'll rotate through sources to get variety
    rss_feeds = [
        ('TechCrunch', 'https://techcrunch.com/feed/'),
        ('The Verge', 'https://www.theverge.com/rss/index.xml'),
        ('Ars Technica', 'https://feeds.arstechnica.com/arstechnica/index'),
        ('Wired', 'https://www.wired.com/feed/rss'),
        ('MIT Technology Review', 'https://www.technologyreview.com/feed/'),
        ('VentureBeat', 'https://venturebeat.com/feed/')
    ]
    
    articles = []
    topics_lower = [t.lower() for t in topics]
    articles_per_source = max(1, limit // len(rss_feeds) + 1)  # Distribute across sources
    
    # Fetch from each source in round-robin fashion
    for source_name, feed_url in rss_feeds:
        if len(articles) >= limit:
            break
            
        try:
            logger.debug(f"Fetching RSS from {source_name}")
            feed = feedparser.parse(feed_url)
            
            source_articles = 0
            for entry in feed.entries[:15]:  # Check first 15 from each source
                if source_articles >= articles_per_source:
                    break  # Move to next source for diversity
                
                if len(articles) >= limit:
                    break
                
                # Check if article is relevant to topics
                title = entry.get('title', '')
                summary = entry.get('summary', entry.get('description', ''))
                
                # Remove HTML tags from summary
                import re
                summary_clean = re.sub('<[^<]+?>', '', summary)
                
                # Simple topic matching
                text_to_check = (title + ' ' + summary_clean).lower()
                is_relevant = any(topic in text_to_check for topic in topics_lower)
                
                if not is_relevant:
                    continue
                
                # Skip if title too short
                if len(title) < 20:
                    continue
                
                # Get publish date
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if published:
                    pub_date = datetime(*published[:6]).isoformat() + 'Z'
                else:
                    pub_date = datetime.now().isoformat() + 'Z'
                
                # Check if article is recent (last 48 hours preferred)
                try:
                    if published:
                        article_date = datetime(*published[:6])
                        age_hours = (datetime.now() - article_date).total_seconds() / 3600
                        if age_hours > 72:  # Skip articles older than 3 days
                            continue
                except:
                    pass
                
                articles.append({
                    'title': title,
                    'summary': summary_clean[:200] if summary_clean else '',
                    'source': source_name,
                    'url': entry.get('link', '#'),
                    'published_at': pub_date,
                    'category': 'technology'
                })
                
                source_articles += 1
                
        except Exception as e:
            logger.warning(f"Failed to fetch RSS from {source_name}: {e}")
            continue
    
    # If we didn't get enough articles, make a second pass without per-source limits
    if len(articles) < limit:
        for source_name, feed_url in rss_feeds:
            if len(articles) >= limit:
                break
            
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:15]:
                    if len(articles) >= limit:
                        break
                    
                    # Check if already added
                    url = entry.get('link', '')
                    if any(a['url'] == url for a in articles):
                        continue
                    
                    title = entry.get('title', '')
                    summary = entry.get('summary', entry.get('description', ''))
                    
                    import re
                    summary_clean = re.sub('<[^<]+?>', '', summary)
                    
                    text_to_check = (title + ' ' + summary_clean).lower()
                    is_relevant = any(topic in text_to_check for topic in topics_lower)
                    
                    if not is_relevant or len(title) < 20:
                        continue
                    
                    published = entry.get('published_parsed') or entry.get('updated_parsed')
                    if published:
                        pub_date = datetime(*published[:6]).isoformat() + 'Z'
                    else:
                        pub_date = datetime.now().isoformat() + 'Z'
                    
                    articles.append({
                        'title': title,
                        'summary': summary_clean[:200] if summary_clean else '',
                        'source': source_name,
                        'url': url,
                        'published_at': pub_date,
                        'category': 'technology'
                    })
                    
            except Exception as e:
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
