from collections import defaultdict
from datetime import datetime
from typing import Dict, List


def build_digest(entries: List[dict]) -> Dict[str, List[dict]]:
    grouped = defaultdict(list)
    for entry in entries:
        feed_title = entry.get("feed_title", "Unknown Feed")
        grouped[feed_title].append(entry)

    for feed_title in grouped:
        grouped[feed_title].sort(
            key=lambda e: e.get("published") or datetime.min,
            reverse=True,
        )

    return dict(grouped)


def format_digest_message(digest: Dict[str, List[dict]]) -> str:
    if not digest:
        return "<b>📰 Daily Digest</b>\n\nNo new entries today."

    total = sum(len(entries) for entries in digest.values())
    parts = [f"<b>📰 Daily Digest</b> — {total} new entries\n"]

    for feed_title, entries in sorted(digest.items()):
        parts.append(f"\n<b>📡 {feed_title}</b>")
        for entry in entries[:5]:
            title = entry.get("title", "No title")
            link = entry.get("link", "")
            if link:
                parts.append(f'  • <a href="{link}">{title}</a>')
            else:
                parts.append(f"  • {title}")
        if len(entries) > 5:
            parts.append(f"  ... and {len(entries) - 5} more")

    return "\n".join(parts)


def format_digest_stats(digest: Dict[str, List[dict]]) -> str:
    total = sum(len(entries) for entries in digest.values())
    feed_count = len(digest)
    lines = [
        f"<b>📊 Digest Stats</b>",
        f"Feeds with updates: {feed_count}",
        f"Total new entries: {total}",
    ]
    for feed_title, entries in sorted(digest.items()):
        lines.append(f"  • {feed_title}: {len(entries)} entries")
    return "\n".join(lines)
