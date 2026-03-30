import json
import feedparser
from typing import List, Dict, Any
from db import fetch_config

def get_config() -> Dict[str, Any]:
    return fetch_config()

def scrape_articles_for_active_group() -> List[Dict[str, str]]:
    config = get_config()
    active_group_key = config.get("active_group", "ai")
    groups = config.get("groups", {})

    if active_group_key not in groups:
        raise ValueError(f"Group '{active_group_key}' not found in config.json")

    group_data = groups[active_group_key]
    rss_feeds = group_data.get("rss_feeds", [])

    articles = []
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                articles.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "source": feed.feed.get("title", feed_url)
                })
        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")

    return articles
