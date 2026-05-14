"""
recommender.py — Recommendation engine for Optima Assistant.

Stores user preferences in a local JSON file and recommends
Movies/Shows, Music, Books, and YouTube videos using free APIs.
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime

PREFS_FILE = os.path.join(os.path.dirname(__file__), "preferences.json")

# ── Default preference profile ───────────────────────────────────────────────

DEFAULT_PREFS = {
    "profile": {
        "favorite_genres":   [],   # e.g. ["action", "comedy"]
        "favorite_artists":  [],   # music artists
        "favorite_authors":  [],   # book authors
        "languages":         ["en"],
    },
    "ratings": {
        "movies":  {},   # {"Movie Title": 4}
        "music":   {},
        "books":   {},
        "youtube": {},
    },
    "history": [],       # [{"type": "movie", "title": "...", "ts": "..."}]
    "keyword_freq": {},  # {"action": 5, "thriller": 2} — auto-learned
}


# ── Storage ──────────────────────────────────────────────────────────────────

def _load() -> dict:
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge missing keys from DEFAULT_PREFS
            for k, v in DEFAULT_PREFS.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_PREFS))  # deep copy


def _save(prefs: dict):
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2, ensure_ascii=False)


# ── Preference helpers ────────────────────────────────────────────────────────

def get_preferences() -> dict:
    return _load()


def set_profile(key: str, values: list):
    """Set a profile field (e.g. favorite_genres, favorite_artists)."""
    prefs = _load()
    prefs["profile"][key] = values
    _save(prefs)


def rate_item(category: str, title: str, rating: int):
    """Rate an item 1-5. category: movies | music | books | youtube"""
    prefs = _load()
    prefs["ratings"].setdefault(category, {})[title] = max(1, min(5, rating))
    _save(prefs)


def log_history(item_type: str, title: str, keywords: list = None):
    """Log a viewed/requested item and update keyword frequency."""
    prefs = _load()
    prefs["history"].append({
        "type":  item_type,
        "title": title,
        "ts":    datetime.now().isoformat(),
    })
    # Keep last 200 history items
    prefs["history"] = prefs["history"][-200:]

    # Update keyword frequency for auto-learning
    for kw in (keywords or []):
        kw = kw.lower().strip()
        if kw:
            prefs["keyword_freq"][kw] = prefs["keyword_freq"].get(kw, 0) + 1

    _save(prefs)


def get_top_keywords(n=5) -> list:
    prefs = _load()
    freq  = prefs.get("keyword_freq", {})
    return sorted(freq, key=freq.get, reverse=True)[:n]


# ── Fetch helpers ─────────────────────────────────────────────────────────────

def _fetch_json(url: str, headers: dict = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {
        "User-Agent": "OptimaAssistant/1.0"
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


# ── Movie / Show recommendations (TMDB free API) ──────────────────────────────

TMDB_KEY = "6f7f13a14b46b3150139feaa02144f47"   # https://www.themoviedb.org/settings/api (free)

def recommend_movies(genre: str = None, max_items: int = 5) -> list:
    prefs    = _load()
    genres   = [genre] if genre else prefs["profile"].get("favorite_genres", [])
    keyword  = get_top_keywords(1)
    query    = (genres[0] if genres else (keyword[0] if keyword else "popular"))

    # Genre ID map (TMDB)
    genre_map = {
        "action": 28, "comedy": 35, "drama": 18, "horror": 27,
        "romance": 10749, "thriller": 53, "sci-fi": 878,
        "animation": 16, "documentary": 99, "fantasy": 14,
    }
    genre_id = genre_map.get(query.lower())

    if genre_id:
        url = (f"https://api.themoviedb.org/3/discover/movie"
               f"?api_key={TMDB_KEY}&with_genres={genre_id}"
               f"&sort_by=popularity.desc&page=1")
    else:
        url = (f"https://api.themoviedb.org/3/search/movie"
               f"?api_key={TMDB_KEY}&query={urllib.parse.quote(query)}&page=1")

    data    = _fetch_json(url)
    results = data.get("results", [])[:max_items]
    movies  = []
    rated   = prefs["ratings"].get("movies", {})

    for m in results:
        title = m.get("title", "")
        movies.append({
            "title":   title,
            "year":    (m.get("release_date") or "")[:4],
            "rating":  m.get("vote_average", "?"),
            "your_rating": rated.get(title),
            "overview": (m.get("overview") or "")[:120] + "…",
        })
    return movies


# ── Music recommendations (iTunes Search API — free, no key) ─────────────────

def recommend_music(artist: str = None, max_items: int = 5) -> list:
    prefs   = _load()
    artists = [artist] if artist else prefs["profile"].get("favorite_artists", [])
    keyword = get_top_keywords(1)
    query   = artists[0] if artists else (keyword[0] if keyword else "top hits")

    url  = (f"https://itunes.apple.com/search"
            f"?term={urllib.parse.quote(query)}&media=music&limit={max_items}")
    data = _fetch_json(url)
    rated = prefs["ratings"].get("music", {})

    results = []
    for t in data.get("results", [])[:max_items]:
        title = f"{t.get('trackName','')} — {t.get('artistName','')}"
        results.append({
            "title":       title,
            "artist":      t.get("artistName", ""),
            "track":       t.get("trackName", ""),
            "album":       t.get("collectionName", ""),
            "preview_url": t.get("previewUrl", ""),
            "your_rating": rated.get(title),
        })
    return results


# ── Book recommendations (Open Library — free, no key) ───────────────────────

def recommend_books(topic: str = None, max_items: int = 5) -> list:
    prefs   = _load()
    authors = prefs["profile"].get("favorite_authors", [])
    keyword = get_top_keywords(1)
    query   = topic or (authors[0] if authors else (keyword[0] if keyword else "bestseller"))

    url  = (f"https://openlibrary.org/search.json"
            f"?q={urllib.parse.quote(query)}&limit={max_items}&fields=title,author_name,first_publish_year,subject")
    data = _fetch_json(url)
    rated = prefs["ratings"].get("books", {})

    results = []
    for b in data.get("docs", [])[:max_items]:
        title = b.get("title", "")
        results.append({
            "title":       title,
            "author":      ", ".join(b.get("author_name", [])[:2]),
            "year":        b.get("first_publish_year", "?"),
            "your_rating": rated.get(title),
        })
    return results


# ── YouTube recommendations (YouTube Data API v3 — free 10k/day) ─────────────

YOUTUBE_KEY = "YOUR_YOUTUBE_API_KEY"   # https://console.cloud.google.com (free)

def recommend_youtube(topic: str = None, max_items: int = 5) -> list:
    prefs   = _load()
    keyword = get_top_keywords(1)
    query   = topic or (keyword[0] if keyword else "trending")

    url  = (f"https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&q={urllib.parse.quote(query)}"
            f"&type=video&maxResults={max_items}&key={YOUTUBE_KEY}")
    data = _fetch_json(url)
    rated = prefs["ratings"].get("youtube", {})

    results = []
    for item in data.get("items", []):
        vid_id = item["id"].get("videoId", "")
        title  = item["snippet"].get("title", "")
        results.append({
            "title":       title,
            "channel":     item["snippet"].get("channelTitle", ""),
            "url":         f"https://youtube.com/watch?v={vid_id}",
            "your_rating": rated.get(title),
        })
    return results