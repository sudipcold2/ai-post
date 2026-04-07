import json
import feedparser
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from db import fetch_config

def get_config() -> Dict[str, Any]:
    return fetch_config()

def _normalize_title(title: str) -> str:
    """Normalize a title for comparison: lowercase, strip punctuation."""
    import re
    return re.sub(r'[^a-z0-9\s]', '', title.lower()).strip()

def _titles_are_similar(a: str, b: str, threshold: float = 0.6) -> bool:
    """Check if two titles are similar using word overlap ratio."""
    words_a = set(_normalize_title(a).split())
    words_b = set(_normalize_title(b).split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b)
    smaller = min(len(words_a), len(words_b))
    return (overlap / smaller) >= threshold if smaller > 0 else False

def _get_article_age_hours(entry) -> float:
    """Get article age in hours. Returns 999 if no date found."""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        try:
            from time import mktime
            pub_time = datetime.fromtimestamp(mktime(published), tz=timezone.utc)
            age = (datetime.now(timezone.utc) - pub_time).total_seconds() / 3600
            return max(0, age)
        except:
            pass
    return 999  # Unknown age — treat as old

def _freshness_score(age_hours: float) -> float:
    """Score from 1.0 (fresh) to 0.1 (stale). Articles < 24h get top score."""
    if age_hours <= 12:
        return 1.0
    elif age_hours <= 24:
        return 0.85
    elif age_hours <= 48:
        return 0.5
    elif age_hours <= 72:
        return 0.3
    else:
        return 0.1

def _deduplicate_articles(articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove articles with similar titles, keeping the one with better freshness."""
    if not articles:
        return articles
    
    unique = []
    for article in articles:
        is_dup = False
        for existing in unique:
            if _titles_are_similar(article["title"], existing["title"]):
                # Keep the fresher one
                if article.get("_freshness", 0) > existing.get("_freshness", 0):
                    unique.remove(existing)
                    unique.append(article)
                is_dup = True
                break
        if not is_dup:
            unique.append(article)
    return unique

def scrape_articles_for_active_group() -> List[Dict[str, str]]:
    config = get_config()
    active_group_key = config.get("active_group", "ai")
    groups = config.get("groups", {})

    if active_group_key not in groups:
        raise ValueError(f"Group '{active_group_key}' not found in config")

    group_data = groups[active_group_key]
    rss_feeds = group_data.get("rss_feeds", [])

    articles = []
    feed_errors = []
    
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and not feed.entries:
                feed_errors.append({"feed": feed_url, "error": str(feed.bozo_exception)})
                continue
            
            feed_name = feed.feed.get("title", feed_url)
            
            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                if not title:
                    continue
                    
                age_hours = _get_article_age_hours(entry)
                freshness = _freshness_score(age_hours)
                
                articles.append({
                    "title": title,
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "source": feed_name,
                    "_freshness": freshness,
                    "_age_hours": age_hours
                })
        except Exception as e:
            feed_errors.append({"feed": feed_url, "error": str(e)})
            print(f"[FEED ERROR] {feed_url}: {e}")

    if feed_errors:
        print(f"[SCRAPER] {len(feed_errors)} feed(s) had errors:")
        for err in feed_errors:
            print(f"  ✗ {err['feed'][:60]}... → {err['error'][:80]}")
    
    # Deduplicate similar titles
    articles = _deduplicate_articles(articles)
    
    # Sort by freshness (freshest first)
    articles.sort(key=lambda a: a.get("_freshness", 0), reverse=True)
    
    print(f"[SCRAPER] {len(articles)} unique articles after dedup (from {len(rss_feeds)} feeds)")
    
    # Clean internal fields before returning
    for article in articles:
        article.pop("_freshness", None)
        article.pop("_age_hours", None)

    return articles
