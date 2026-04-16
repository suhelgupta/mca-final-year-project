import json
import urllib.request
import urllib.parse


def _fetch_json(url, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def latest_news(category="all", max_items=5):
    """Fetch the latest short-format news items."""
    category = urllib.parse.quote(category)
    url = f"https://inshorts.deta.dev/news?category={category}"
    data = _fetch_json(url)
    if data.get("success") is not True:
        raise RuntimeError("Unable to fetch news right now.")

    articles = []
    for item in data.get("data", [])[:max_items]:
        articles.append({
            "title": item.get("title"),
            "content": item.get("content"),
            "source": item.get("source"),
            "read_more_url": item.get("readMoreUrl"),
        })
    return articles


def latest_news_summary(category="all", max_items=5):
    """Return a simple text summary of the latest news."""
    articles = latest_news(category=category, max_items=max_items)
    lines = []
    for idx, article in enumerate(articles, start=1):
        lines.append(f"{idx}. {article['title']}\n   {article['content']}")
    return "\n\n".join(lines)

if __name__ == "__main__":
    print(latest_news_summary(category="", max_items=3))