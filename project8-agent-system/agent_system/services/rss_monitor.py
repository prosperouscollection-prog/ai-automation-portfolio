"""RSS feed monitoring utilities."""

from __future__ import annotations

import feedparser


class RSSMonitor:
    """Fetch and normalize RSS entries from vendor changelogs."""

    def fetch_many(self, feeds: dict[str, str]) -> dict[str, list[dict[str, str]]]:
        output: dict[str, list[dict[str, str]]] = {}
        for name, url in feeds.items():
            try:
                parsed = feedparser.parse(url)
                output[name] = [
                    {
                        "title": getattr(entry, "title", ""),
                        "link": getattr(entry, "link", ""),
                        "published": getattr(entry, "published", ""),
                        "summary": getattr(entry, "summary", "")[:500],
                    }
                    for entry in parsed.entries[:5]
                ]
            except Exception:  # noqa: BLE001
                output[name] = []
        return output
