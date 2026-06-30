"""
Publisher — main entry. Runs scraper + analyzer, writes:
  - data/analysis.json        (latest snapshot)
  - data/history/<timestamp>.json  (history archive)
  - docs/data/analysis.json   (Pages-readable copy)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as `python src/publisher.py` from project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import scraper, analyzer  # noqa: E402


def _atomic_write_json(path: Path, payload: dict) -> None:
    """Write JSON atomically: write to .tmp then rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _trim_for_pages(payload: dict) -> dict:
    """Trim the payload for GitHub Pages (smaller file = faster load).
    Keep only top 50 articles, full summary still there."""
    return {
        "generated_at": payload["generated_at"],
        "article_count": payload["article_count"],
        "summary": payload["summary"],
        "articles": payload["articles"][:50],
    }


def run() -> dict:
    """Main entry. Returns the analysis payload (also written to disk)."""
    print("=" * 60)
    print("Market News Analyzer — run started")
    print("=" * 60)

    articles = scraper.fetch_all()
    if not articles:
        print("[publisher] no articles scraped — writing empty payload")
    payload = analyzer.analyze_batch(articles)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    data_dir = ROOT / "data"
    history_dir = data_dir / "history"

    # Latest snapshot
    _atomic_write_json(data_dir / "analysis.json", payload)
    # History archive
    _atomic_write_json(history_dir / f"{ts}.json", payload)
    # Pages copy (trimmed)
    pages_payload = _trim_for_pages(payload)
    _atomic_write_json(ROOT / "docs" / "data" / "analysis.json", pages_payload)

    # Print summary
    s = payload["summary"]
    print(f"\n--- SUMMARY ---")
    print(f"Articles:        {payload['article_count']}")
    print(f"Market label:    {s.get('market_sentiment_label', 'n/a')} "
          f"(score {s.get('market_sentiment_score', 0):+.3f})")
    print(f"Label mix:       {s.get('label_distribution', {})}")
    print(f"Top coin:        {s.get('top_coins', [{}])[0].get('coin', 'n/a')}")
    print(f"Top topic:       {s.get('top_topics', [{}])[0].get('topic', 'n/a')}")
    print("=" * 60)

    return payload


if __name__ == "__main__":
    run()
