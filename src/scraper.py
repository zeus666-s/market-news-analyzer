"""
News scraper — pulls crypto news from public sources (no API key needed).
Sources:
  - CryptoPanic public API (latest posts, no auth required for public read)
  - CoinDesk RSS (https://www.coindesk.com/arc/outboundfeeds/rss/)
  - Cointelegraph RSS (https://cointelegraph.com/rss)
  - The Block RSS (https://www.theblock.co/rss.xml)

Returns a list of normalized article dicts:
  {source, title, url, published_at, summary, raw}
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

try:
    import feedparser  # type: ignore
except ImportError:  # pragma: no cover
    feedparser = None


USER_AGENT = "market-news-analyzer/1.0 (+https://github.com)"
HTTP_TIMEOUT = 20

RSS_FEEDS = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("The Block", "https://www.theblock.co/rss.xml"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
]

CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/?public=true"


def _http_get(url: str, accept: str = "application/json") -> dict | str:
    """Minimal HTTP GET with timeout + UA. Returns parsed JSON or raw text."""
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    if accept.startswith("application/json"):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"_raw": body}
    return body


def _normalize_rss(source: str, entry: Any) -> dict | None:
    """Convert a feedparser entry into our normalized shape."""
    title = (getattr(entry, "title", "") or "").strip()
    link = (getattr(entry, "link", "") or "").strip()
    if not title or not link:
        return None
    summary = (getattr(entry, "summary", "") or "")
    summary = re.sub(r"<[^>]+>", "", summary).strip()
    if len(summary) > 500:
        summary = summary[:497] + "..."
    published = getattr(entry, "published_parsed", None) or getattr(
        entry, "updated_parsed", None
    )
    if published:
        published_at = datetime(*published[:6], tzinfo=timezone.utc).isoformat()
    else:
        published_at = datetime.now(timezone.utc).isoformat()
    return {
        "source": source,
        "title": title,
        "url": link,
        "published_at": published_at,
        "summary": summary,
    }


def fetch_rss() -> list[dict]:
    """Pull RSS feeds. Returns list of normalized articles."""
    if feedparser is None:
        print("[scraper] feedparser not installed — skipping RSS")
        return []
    out: list[dict] = []
    for source, url in RSS_FEEDS:
        try:
            print(f"[scraper] RSS fetch: {source}")
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:15]:  # cap per source
                norm = _normalize_rss(source, entry)
                if norm:
                    out.append(norm)
        except Exception as e:
            print(f"[scraper] RSS error {source}: {e}")
    return out


def fetch_cryptopanic() -> list[dict]:
    """Pull CryptoPanic public posts. Public endpoint, no key required."""
    out: list[dict] = []
    try:
        print("[scraper] CryptoPanic fetch")
        data = _http_get(CRYPTOPANIC_URL)
        if not isinstance(data, dict) or "results" not in data:
            return []
        for post in data.get("results", [])[:30]:
            title = (post.get("title") or "").strip()
            url = (post.get("url") or "").strip()
            if not title or not url:
                continue
            published_at = post.get("published_at") or datetime.now(timezone.utc).isoformat()
            kind = post.get("kind", "news")
            out.append(
                {
                    "source": f"CryptoPanic/{kind}",
                    "title": title,
                    "url": url,
                    "published_at": published_at,
                    "summary": "",
                }
            )
    except (URLError, HTTPError, TimeoutError) as e:
        print(f"[scraper] CryptoPanic error: {e}")
    return out


def fetch_all() -> list[dict]:
    """Fetch from all sources, dedupe by URL, return sorted newest-first."""
    started = time.time()
    all_articles: list[dict] = []
    all_articles.extend(fetch_rss())
    all_articles.extend(fetch_cryptopanic())
    # dedupe
    seen = set()
    deduped: list[dict] = []
    for a in all_articles:
        if a["url"] in seen:
            continue
        seen.add(a["url"])
        deduped.append(a)
    # sort newest first
    deduped.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    elapsed = time.time() - started
    print(f"[scraper] fetched {len(deduped)} unique articles in {elapsed:.1f}s")
    return deduped


if __name__ == "__main__":
    arts = fetch_all()
    print(f"\nTotal: {len(arts)} articles")
    for a in arts[:5]:
        print(f"  [{a['source']}] {a['title'][:80]}")
