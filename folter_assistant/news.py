import json
import urllib.request
import urllib.parse

API_KEY = "664f8d8eb9da48b6b4508a79a9126be9"   # ← paste your key

def _fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "FolterAssistant/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def latest_news(category="general", max_items=5):
    """Fetch latest news from NewsAPI."""
    category = category if category in (
        "business", "entertainment", "general",
        "health", "science", "sports", "technology"
    ) else "general"

    url = (
        f"https://newsapi.org/v2/top-headlines"
        f"?category={urllib.parse.quote(category)}"
        f"&pageSize={max_items}"
        f"&language=en"
        f"&apiKey={API_KEY}"
    )
    data = _fetch_json(url)

    if data.get("status") != "ok":
        raise RuntimeError(f"News API error: {data.get('message', 'Unknown error')}")

    articles = []
    for item in data.get("articles", [])[:max_items]:
        articles.append({
            "title":        item.get("title", "No title"),
            "content":      item.get("description") or item.get("content") or "",
            "source":       item.get("source", {}).get("name", ""),
            "read_more_url": item.get("url", ""),
        })
    return articles


def latest_news_summary(category="general", max_items=5):
    """Return a plain-text summary of latest news."""
    articles = latest_news(category=category, max_items=max_items)
    lines = []
    for idx, article in enumerate(articles, start=1):
        lines.append(f"{idx}. {article['title']}\n   {article['content']}")
    return "\n\n".join(lines)


if __name__ == "__main__":
    print(latest_news_summary(category="general", max_items=3))