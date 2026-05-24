from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from app.config import settings
from app.summarizer import ai_summary, clean_text

BASE_URL = "https://www.geo.tv/"

# RSS URLs are kept configurable/fallback-friendly because media sites often change feed IDs.
RSS_FEEDS = {
    "Pakistan": "https://www.geo.tv/rss/1/1",
    "World": "https://www.geo.tv/rss/1/3",
    "Business": "https://www.geo.tv/rss/1/4",
    "Sports": "https://www.geo.tv/rss/1/5",
    "Entertainment": "https://www.geo.tv/rss/1/7",
    "Tech": "https://www.geo.tv/rss/1/8",
    "Health": "https://www.geo.tv/rss/1/10",
}

CATEGORY_KEYWORDS = {
    "Pakistan": ["pakistan", "ispr", "punjab", "sindh", "balochistan", "khyber", "karachi", "lahore", "islamabad", "pm ", "govt"],
    "World": ["world", "us", "iran", "china", "india", "russia", "gaza", "israel", "trump", "europe"],
    "Business": ["business", "economy", "budget", "petrol", "rupee", "dollar", "market", "tax", "imf", "finance"],
    "Sports": ["sports", "cricket", "pcb", "football", "match", "champions", "psl", "fifa", "tennis"],
    "Tech": ["tech", "ai", "software", "gadgets", "apple", "google", "microsoft", "openai", "meta"],
    "Health": ["health", "doctor", "hospital", "disease", "virus", "vaccine"],
    "Entertainment": ["entertainment", "actor", "film", "music", "hollywood", "showbiz", "royal"],
}


def _today_iso() -> str:
    return datetime.now().date().isoformat()


def _parse_date(entry) -> str | None:
    raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except Exception:
        return None


def _category_from_text(text: str) -> str:
    lowered = text.lower()
    scores = {}
    for category, words in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for w in words if w in lowered)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Latest"


def fetch_from_rss(today_only: bool = True) -> list[dict]:
    items: list[dict] = []
    today = _today_iso()

    for category, feed_url in RSS_FEEDS.items():
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            continue

        for entry in feed.entries[: settings.MAX_ITEMS_PER_CATEGORY * 2]:
            published = _parse_date(entry)
            if today_only and published and published != today:
                continue

            title = clean_text(getattr(entry, "title", ""))
            link = getattr(entry, "link", "")
            raw_summary = clean_text(getattr(entry, "summary", ""))
            if not title or not link:
                continue
            summary, why = ai_summary(title, raw_summary)
            items.append(
                {
                    "category": category,
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "why_it_matters": why,
                    "published": published,
                }
            )
    return items


def fetch_from_homepage() -> list[dict]:
    """Fallback: parses Geo homepage headings if RSS is unavailable."""
    headers = {"User-Agent": "Mozilla/5.0 GeoNewsBriefingStudentProject/1.0"}
    res = requests.get(BASE_URL, headers=headers, timeout=settings.REQUEST_TIMEOUT)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    seen: set[str] = set()
    items: list[dict] = []

    for a in soup.find_all("a", href=True):
        title = clean_text(a.get_text(" "))
        href = urljoin(BASE_URL, a["href"])
        if len(title) < 18 or "geo" == title.lower() or href in seen:
            continue
        if "geo.tv" not in href:
            continue
        seen.add(href)
        category = _category_from_text(title + " " + href)
        summary, why = ai_summary(title, title)
        items.append(
            {
                "category": category,
                "title": title,
                "link": href,
                "summary": summary,
                "why_it_matters": why,
                "published": _today_iso(),
            }
        )
        if len(items) >= 50:
            break

    return items


def get_briefing(today_only: bool = True) -> dict:
    items = fetch_from_rss(today_only=today_only)
    if not items:
        items = fetch_from_homepage()

    grouped: dict[str, list[dict]] = defaultdict(list)
    seen_titles: set[str] = set()

    for item in items:
        key = item["title"].lower().strip()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        if len(grouped[item["category"]]) < settings.MAX_ITEMS_PER_CATEGORY:
            grouped[item["category"]].append(item)

    ordered = dict(sorted(grouped.items(), key=lambda x: x[0]))
    return {"date": _today_iso(), "total": sum(len(v) for v in ordered.values()), "categories": ordered}
