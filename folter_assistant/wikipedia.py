import json
import urllib.request
import urllib.parse


def _fetch_json(url, timeout=20):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def search_wikipedia(query, sentences=2):
    """Fetch a Wikipedia summary for a search query."""
    if not query:
        raise ValueError("Query cannot be empty.")

    title = urllib.parse.quote(query)
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    data = _fetch_json(url)
    if data.get("type") == "disambiguation":
        return {
            "title": data.get("title"),
            "extract": data.get("extract"),
            "description": data.get("description", ""),
            "disambiguation": True,
        }

    return {
        "title": data.get("title", query),
        "description": data.get("description", ""),
        "extract": data.get("extract", ""),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
    }


def search_wikipedia_summary(query, sentences=2):
    data = search_wikipedia(query, sentences=sentences)
    extract = data.get("extract", "No summary available.")
    return f"{data.get('title', query)}:\n{extract}\nSource: {data.get('url', '')}"
