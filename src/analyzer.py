"""
Sentiment + keyword analyzer for crypto news.
Lightweight, deterministic, no ML model dependency.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any


# Crypto-specific sentiment lexicon. Weight range: -3 (very bearish) to +3 (very bullish).
POSITIVE_TERMS: dict[str, int] = {
    "surge": 3, "surges": 3, "soar": 3, "soars": 3, "rally": 3, "rallies": 3,
    "breakthrough": 3, "milestone": 2, "ath": 3, "all-time high": 3, "record high": 3,
    "bullish": 3, "moon": 2, "mooning": 3, "adoption": 2, "approved": 2, "approval": 2,
    "partnership": 2, "integrate": 2, "integration": 2, "launch": 1, "launches": 1,
    "launched": 1, "innovation": 2, "upgrade": 1, "upgrades": 1, "win": 2, "wins": 2,
    "growth": 2, "growing": 2, "profit": 2, "profits": 2, "gain": 1, "gains": 1,
    "institutional": 2, "etf approval": 3, "etf approved": 3, "accumulate": 2,
    "accumulation": 2, "buying": 1, "buy": 1, "buys": 1, "demand": 2, "optimism": 2,
    "optimistic": 2, "support": 1, "supports": 1, "positive": 2, "boost": 2, "boosts": 2,
    "boosted": 2, "recover": 1, "recovery": 1, "recovered": 1, "strong": 1,
    "strength": 1, "leading": 1, "leads": 1, "outperform": 2, "outperforms": 2,
    "successful": 2, "success": 2, "secure": 1, "secured": 1, "trust": 1, "trusted": 1,
}

NEGATIVE_TERMS: dict[str, int] = {
    "crash": -3, "crashes": -3, "crashed": -3, "plunge": -3, "plunges": -3,
    "plummet": -3, "plummets": -3, "tank": -2, "tanks": -2, "dump": -2, "dumps": -2,
    "bearish": -3, "collapse": -3, "collapses": -3, "collapsed": -3, "fraud": -3,
    "scam": -3, "rugpull": -3, "rug pull": -3, "hack": -3, "hacked": -3,
    "exploit": -3, "exploited": -3, "stolen": -3, "theft": -3, "ban": -2,
    "banned": -2, "bans": -2, "ban": -2, "ban": -2, "warning": -1, "warns": -1,
    "warned": -1, "lawsuit": -2, "sued": -2, "sec charges": -3, "investigation": -2,
    "investigated": -2, "investigate": -2, "fears": -2, "fear": -1, "panic": -2,
    "concerns": -1, "concern": -1, "concerned": -1, "risk": -1, "risks": -1,
    "risky": -1, "loss": -2, "losses": -2, "lost": -2, "lose": -1, "loses": -1,
    "losing": -1, "drop": -1, "drops": -1, "dropped": -1, "decline": -2,
    "declines": -2, "declined": -2, "fall": -1, "falls": -1, "fell": -1, "down": -1,
    "weak": -1, "weakness": -1, "struggle": -2, "struggles": -2, "fail": -2,
    "fails": -2, "failed": -2, "failure": -2, "liquidation": -2, "liquidations": -2,
    "delist": -2, "delisting": -2, "delisted": -2, "halt": -2, "halted": -2,
    "negative": -1, "bear": -1, "bears": -1, "underperform": -2, "underperforms": -2,
    "sell": -1, "selling": -1, "sells": -1, "sell-off": -2, "selloff": -2,
}

# Coins to track. Matched as whole words (case-insensitive).
TRACKED_COINS = [
    "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "binance", "bnb",
    "ripple", "xrp", "cardano", "ada", "dogecoin", "doge", "polkadot", "dot",
    "tron", "trx", "avalanche", "avax", "polygon", "matic", "chainlink", "link",
    "litecoin", "ltc", "bitcoin cash", "bch", "near", "near protocol", "uniswap", "uni",
    "cosmos", "atom", "monero", "xmr", "stellar", "xlm", "algorand", "algo",
    "filecoin", "fil", "aptos", "apt", "sui", "arbitrum", "arb", "optimism", "op",
]

# Common crypto terms (extracted as topics/keywords).
TOPIC_TERMS = [
    "defi", "nft", "nfts", "etf", "spot etf", "futures", "staking", "yield",
    "lending", "dex", "cex", "wallet", "exchange", "exchanges", "regulation",
    "regulatory", "sec", "cftc", "fed", "interest rate", "inflation", "macro",
    "layer 2", "l2", "rollup", "zk", "zero knowledge", "bridge", "cross-chain",
    "tvl", "liquidity", "stablecoin", "usdt", "usdc", "dai", "fiat", "on-chain",
    "onchain", "mining", "miner", "miners", "halving", "pow", "pos", "validator",
    "validators", "mainnet", "testnet", "smart contract", "dapp", "dapps",
    "tokenization", "rwa", "real world assets", "ai", "artificial intelligence",
    "memecoin", "memecoin", "gamefi", "metaverse", "dao", "governance",
]


def _tokenize(text: str) -> list[str]:
    """Lowercase + split on non-alphanumeric, keep multi-word phrases intact later."""
    text = text.lower()
    # Replace punctuation with space, keep digits & letters
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    return [t for t in text.split() if t]


def score_article(title: str, summary: str = "") -> dict[str, Any]:
    """Score one article. Returns dict with score, hits, matched_terms."""
    text = f"{title}\n{summary}".lower()
    score = 0
    pos_hits: list[str] = []
    neg_hits: list[str] = []

    # Multi-word phrases first
    for term, weight in POSITIVE_TERMS.items():
        if " " in term and term in text:
            score += weight
            pos_hits.append(term)
    for term, weight in NEGATIVE_TERMS.items():
        if " " in term and term in text:
            score += weight
            neg_hits.append(term)

    # Single-word tokens
    tokens = set(_tokenize(text))
    for term, weight in POSITIVE_TERMS.items():
        if " " not in term and term in tokens:
            score += weight
            pos_hits.append(term)
    for term, weight in NEGATIVE_TERMS.items():
        if " " not in term and term in tokens:
            score += weight
            neg_hits.append(term)

    # Normalize score roughly to [-1, 1]
    norm = max(-1.0, min(1.0, score / 8.0))
    if score > 0:
        label = "bullish"
    elif score < 0:
        label = "bearish"
    else:
        label = "neutral"

    return {
        "score": score,
        "normalized": round(norm, 3),
        "label": label,
        "positive_hits": sorted(set(pos_hits)),
        "negative_hits": sorted(set(neg_hits)),
    }


def extract_coins(text: str) -> list[str]:
    """Return which tracked coins appear in text, in canonical form."""
    text_l = text.lower()
    found: list[str] = []
    seen: set[str] = set()
    for coin in TRACKED_COINS:
        if coin in text_l:
            canonical = coin.upper() if coin in {"btc", "eth", "bnb", "xrp",
                                                  "ada", "doge", "dot", "trx",
                                                  "avax", "matic", "link", "ltc",
                                                  "bch", "uni", "atom", "xmr",
                                                  "xlm", "algo", "fil", "apt",
                                                  "arb", "op", "sol"} else coin.title()
            if canonical not in seen:
                seen.add(canonical)
                found.append(canonical)
    return found


def extract_topics(text: str) -> list[str]:
    """Return which topic terms appear in text."""
    text_l = text.lower()
    return sorted({t for t in TOPIC_TERMS if t in text_l})


def analyze_batch(articles: list[dict]) -> dict[str, Any]:
    """Score + enrich all articles, then aggregate market-level summary."""
    if not articles:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "article_count": 0,
            "summary": {},
            "articles": [],
        }

    enriched: list[dict] = []
    coin_mentions: Counter = Counter()
    topic_mentions: Counter = Counter()
    total_score = 0.0
    label_counts: Counter = Counter()

    for a in articles:
        text = f"{a.get('title', '')} {a.get('summary', '')}"
        s = score_article(a.get("title", ""), a.get("summary", ""))
        coins = extract_coins(text)
        topics = extract_topics(text)
        for c in coins:
            coin_mentions[c] += 1
        for t in topics:
            topic_mentions[t] += 1
        total_score += s["normalized"]
        label_counts[s["label"]] += 1
        enriched.append({**a, "sentiment": s, "coins": coins, "topics": topics})

    avg = total_score / len(articles)
    if avg > 0.15:
        market_label = "bullish"
    elif avg < -0.15:
        market_label = "bearish"
    else:
        market_label = "neutral"

    summary = {
        "market_sentiment_label": market_label,
        "market_sentiment_score": round(avg, 3),
        "label_distribution": dict(label_counts),
        "top_coins": [
            {"coin": c, "mentions": n}
            for c, n in coin_mentions.most_common(10)
        ],
        "top_topics": [
            {"topic": t, "mentions": n}
            for t, n in topic_mentions.most_common(10)
        ],
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(enriched),
        "summary": summary,
        "articles": enriched,
    }


if __name__ == "__main__":
    # Smoke test
    samples = [
        {"title": "Bitcoin surges to new ATH as ETF approval boosts demand",
         "summary": "Institutional buying drives rally", "url": "x", "published_at": "x"},
        {"title": "Ethereum plunges after exploit drains millions",
         "summary": "Hack triggers panic sell-off", "url": "y", "published_at": "x"},
    ]
    out = analyze_batch(samples)
    print(json.dumps(out["summary"], indent=2))
