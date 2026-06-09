from __future__ import annotations

import json
import re
from datetime import datetime, timedelta

MISSION_TERMS = {
    "fashion", "beauty", "style", "runway", "couture", "aesthetic",
    "makeup", "skincare", "vintage", "vogue", "glamour", "apparel",
    "chic", "poetry", "literature", "designer", "archive", "silhouette", "velvet"
}

MISSION_PHRASES = {
    "high fashion", "vintage style", "runway fashion", "aesthetic trend",
    "fashion week", "street style", "archived fashion", "runway review"
}

SHOPPING_TERMS = {
    "shopping", "shop", "store", "stores", "clothing", "product", "products",
    "order", "orders", "checkout", "cart", "coupon", "discount", "sale",
    "delivery", "returns", "exchange", "sizes"
}

SHOPPING_PHRASES = {
    "product info", "order support", "customer support", "customer service",
    "find a store", "store locator", "size guide", "new collection",
    "poco sale", "buy now", "add to cart"
}

class TrendHunter:
    def __init__(self) -> None:
        self.topic_groups = {
            "fashion": ["fashion", "vintage style", "runway fashion", "high fashion", "street style"],
            "beauty": ["beauty", "makeup", "skincare", "glamour", "vogue"],
            "culture": ["aesthetic trend", "poetry", "archived fashion", "runway review", "couture"],
        }
        self.seed_topics = [item for values in self.topic_groups.values() for item in values]

    def default_queries(self) -> list[str]:
        since = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
        return [
            f"fashion OR runway filter:videos min_faves:210 min_retweets:20 min_replies:11 lang:en since:{since}",
            f"beauty OR makeup min_faves:60 min_replies:5 lang:en since:{since}",
            f"couture OR aesthetic filter:videos min_faves:225 min_retweets:24 min_replies:12 lang:en since:{since}",
            f"street style OR vintage min_faves:45 min_replies:5 lang:en since:{since}",
            f"fashion week filter:videos min_faves:210 min_retweets:24 min_replies:10 lang:en since:{since}",
            f"archived fashion filter:images min_faves:175 min_retweets:20 min_replies:9 lang:en since:{since}",
            f"poetry OR vintage filter:images min_faves:170 min_retweets:21 min_replies:8 lang:en since:{since}",
            f"high fashion filter:images min_faves:190 min_retweets:21 min_replies:11 lang:en since:{since}",
            f"vogue OR glamour filter:videos min_faves:130 min_retweets:14 min_replies:7 lang:en since:{since}",
        ]

    def parse_queries(self, raw: str) -> list[str]:
        try:
            parsed = json.loads(raw)
        except Exception:
            return []
        if not isinstance(parsed, list):
            return []
        queries: list[str] = []
        seen = set()
        for item in parsed:
            query = str(item or "").strip()
            if not query or query in seen:
                continue
            if not self._query_is_on_mission(query):
                continue
            seen.add(query)
            queries.append(query)
        return queries

    def _query_is_on_mission(self, query: str) -> bool:
        lowered = (query or "").lower()
        tokens = set(re.findall(r"[a-z]{3,}", lowered))
        has_mission_phrase = any(phrase in lowered for phrase in MISSION_PHRASES)
        if any(phrase in lowered for phrase in SHOPPING_PHRASES):
            return False
        if (tokens & SHOPPING_TERMS) and not has_mission_phrase:
            return False
        return bool((tokens & MISSION_TERMS) or has_mission_phrase)

    def compose_queries(self, memory_briefs: list[str], limit: int = 8) -> list[str]:
        since = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
        queries: list[str] = []
        seen = set()

        def add(query: str) -> None:
            query = " ".join((query or "").split()).strip()
            if not query or query in seen:
                return
            seen.add(query)
            queries.append(query)

        for query in self.default_queries():
            add(query)

        boosted_topics: list[str] = []
        for item in memory_briefs:
            text = (item or "").strip().lower()
            if not text:
                continue
            for match in re.findall(r"[a-z]{4,}", text):
                if match in {"signal", "source", "trend", "memory", "posts", "fresh", "strongest", "ignored"}:
                    continue
                if match in SHOPPING_TERMS or match not in MISSION_TERMS:
                    continue
                boosted_topics.append(match)

        for index, topic in enumerate(boosted_topics[:12]):
            media_filter = "filter:videos" if index % 2 == 0 else "filter:images"
            add(f"{topic} {media_filter} min_faves:150 min_retweets:14 min_replies:6 lang:en since:{since}")

        return queries[:limit]

    def fallback_results(self, queries: list[str]) -> list[dict]:
        results = []
        for query in queries[:6]:
            topic = query.split("min_", 1)[0].replace("lang:en", "").replace("since:", "").strip()
            results.append(
                {
                    "query": query,
                    "topic": topic,
                    "user": "trend-sim",
                    "text": f"{topic.title()} is shifting faster than most people realize. The aesthetic is still evolving.",
                    "url": "",
                    "image_url": "",
                    "simulated": True,
                    "metrics": {"engagement_hint": 1200},
                }
            )
        return results
