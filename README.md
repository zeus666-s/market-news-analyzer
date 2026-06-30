# Crypto Market News Analyzer

Live market-sentiment dashboard built from crypto news headlines. Scrapes
multiple public sources, scores each headline against a curated lexicon, and
publishes a dashboard via GitHub Pages.

**Live:** https://zeus666-s.github.io/market-news-analyzer/

## What it does

1. **Scrapes** crypto news every 4 hours from:
   - CryptoPanic public API
   - CoinDesk, Cointelegraph, The Block, Decrypt, Bitcoin Magazine RSS feeds
2. **Scores** each headline against a positive/negative crypto lexicon
   (weighted terms like `surge: +3`, `crash: -3`, `etf approval: +3`)
3. **Aggregates** per-article scores into a market sentiment label
   (`bullish` / `neutral` / `bearish`) in `[-1, +1]`
4. **Tracks** mentions of 30+ coins and 50+ topics
5. **Publishes** a static dashboard at the GitHub Pages URL above

## Repo layout

```
market-news-analyzer/
├── .github/workflows/update.yml   # runs analyzer every 4h + on push
├── src/
│   ├── scraper.py                 # fetch RSS + CryptoPanic
│   ├── analyzer.py                # sentiment scoring + coin/topic extraction
│   └── publisher.py               # orchestrator, writes JSON output
├── docs/                          # GitHub Pages source
│   ├── index.html                 # dashboard
│   ├── style.css
│   ├── app.js                     # Chart.js renderers
│   └── data/analysis.json         # latest snapshot (auto-updated)
├── data/                          # primary output + history archive
│   ├── analysis.json
│   └── history/<UTC-timestamp>.json
├── .gitignore
├── requirements.txt               # feedparser
└── README.md
```

## Run locally

```bash
pip install -r requirements.txt
python src/publisher.py
# Then open docs/index.html in a browser (it reads ../data/analysis.json or
# docs/data/analysis.json — the publisher writes both).
```

For local dashboard viewing, serve the `docs/` folder over HTTP so the
`fetch()` in `app.js` works:

```bash
cd docs && python3 -m http.server 8000
# → http://localhost:8000
```

## Method notes

- **Sentiment score** = sum of lexicon weights matched in title + summary,
  normalized to `[-1, +1]` by dividing by `8`. Label thresholds: ±0.15.
- **Coin detection** = substring match against a list of 30+ tracked coins
  (case-insensitive, multi-word like "bitcoin cash" handled).
- **Topic detection** = substring match against 50+ crypto terms (defi, etf,
  sec, stablecoin, layer 2, etc).
- **No ML model** — deterministic, fast, dependency-light. Easy to extend
  the lexicon in `src/analyzer.py`.

## Extending

- **Add a feed:** append to `RSS_FEEDS` in `src/scraper.py`.
- **Add a term:** add to `POSITIVE_TERMS` / `NEGATIVE_TERMS` with a weight
  in `src/analyzer.py`. Use `-3..+3` to keep normalization sensible.
- **Track a new coin:** add to `TRACKED_COINS` in `src/analyzer.py`.
- **Change refresh cadence:** edit the cron in
  `.github/workflows/update.yml`.

## Tech

- Python 3.11 stdlib + `feedparser`
- GitHub Actions for scheduling
- GitHub Pages (free static hosting) for the dashboard
- Chart.js (CDN) for gauges and bar charts

## License

MIT
