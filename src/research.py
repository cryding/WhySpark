"""Collect official science-news feed items for WhySpark research discovery.

This module gathers candidate sources only. Keyword overlap is a discovery hint,
not proof that two sources corroborate a factual claim.
"""
from __future__ import annotations

import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "sources.json"
OUTPUT_DIR = ROOT / "artifacts"
STOPWORDS = {
    "about", "after", "also", "been", "from", "have", "into", "more", "over",
    "than", "that", "their", "there", "these", "they", "this", "with", "will",
    "would", "your", "what", "when", "where", "which", "while", "were", "such",
    "some", "only", "because", "could", "nasa", "noaa", "news", "release",
}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        return re.sub(r"\s+", " ", html.unescape(" ".join(self.parts))).strip()


def clean_text(value: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(value or "")
        return parser.text()
    except Exception:
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(node, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in node.iter():
        if _local_name(child.tag) in wanted and child.text and child.text.strip():
            return clean_text(child.text)
    return ""


def _item_link(node) -> str:
    for child in node:
        if _local_name(child.tag) == "link":
            href = child.attrib.get("href", "").strip()
            if href:
                return href
            if child.text and child.text.strip():
                return child.text.strip()
    return ""


def parse_feed(xml_text: str, source_name: str, allowed_hosts: list[str]) -> list[dict]:
    root = ET.fromstring(xml_text)
    allowed = {host.lower() for host in allowed_hosts}
    items = []
    for node in root.iter():
        if _local_name(node.tag) not in {"item", "entry"}:
            continue
        title = _child_text(node, "title")
        link = _item_link(node)
        summary = _child_text(node, "description", "summary", "encoded", "content")
        published = _child_text(node, "pubdate", "published", "updated", "date")
        parsed = urlparse(link)
        host = (parsed.hostname or "").lower()
        if not title or parsed.scheme != "https" or host not in allowed:
            continue
        items.append({
            "source_name": source_name,
            "title": title[:500],
            "url": link,
            "host": host,
            "published_at": normalize_date(published),
            "summary": summary[:2500],
            "evidence_status": "unverified_discovery_candidate",
        })
    return items


def normalize_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, OverflowError):
            return ""


def keywords(text: str) -> set[str]:
    return {
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text or "")
        if word.lower() not in STOPWORDS
    }


def find_related_candidates(items: list[dict], max_pairs: int = 10) -> list[dict]:
    pairs = []
    for i, left in enumerate(items):
        for right in items[i + 1:]:
            if left["host"] == right["host"]:
                continue
            shared = keywords(left["title"] + " " + left["summary"]) & keywords(
                right["title"] + " " + right["summary"]
            )
            if len(shared) >= 3:
                pairs.append({
                    "source_a_url": left["url"],
                    "source_a_title": left["title"],
                    "source_b_url": right["url"],
                    "source_b_title": right["title"],
                    "shared_discovery_terms": sorted(shared),
                    "lexical_overlap_count": len(shared),
                    "status": "candidate_only_not_fact_checked",
                })
    return sorted(pairs, key=lambda pair: pair["lexical_overlap_count"], reverse=True)[:max_pairs]


def run_research() -> dict:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    all_items = []
    feed_results = []
    errors = []
    session = requests.Session()
    session.headers.update({"User-Agent": "WhySparkResearchBot/0.1 (+https://github.com/cryding/WhySpark)"})
    for feed in config["feeds"]:
        try:
            response = session.get(feed["url"], timeout=(10, 25), allow_redirects=True)
            response.raise_for_status()
            final_host = (urlparse(response.url).hostname or "").lower()
            if final_host not in {host.lower() for host in feed["allowed_hosts"]}:
                raise ValueError(f"Feed redirected to unapproved host: {final_host}")
            items = parse_feed(response.text, feed["name"], feed["allowed_hosts"])
            if not items:
                raise ValueError("Feed returned no valid items from the approved host allowlist")
            all_items.extend(items[:30])
            feed_results.append({"name": feed["name"], "status": "ok", "items_found": len(items)})
        except Exception as exc:
            errors.append(f"{feed['name']}: {type(exc).__name__}: {exc}")
            feed_results.append({"name": feed["name"], "status": "failed", "items_found": 0})
    deduped = {item["url"]: item for item in all_items}
    items = list(deduped.values())
    items.sort(key=lambda item: item.get("published_at", ""), reverse=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "WhySpark",
        "mode": "research_discovery_only",
        "paid_services_used": False,
        "feed_results": feed_results,
        "errors": errors,
        "candidate_count": len(items),
        "related_candidates": find_related_candidates(items),
        "items": items[:60],
        "safety_notice": (
            "These are research candidates, not verified facts. Shared keywords do not establish "
            "corroboration. No script, video, or YouTube upload is authorized by this report."
        ),
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "research.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# WhySpark research discovery report", "",
        f"Generated: {report['generated_at']}",
        f"Candidates collected: {report['candidate_count']}", "",
        "> **Not fact-checked.** Keyword overlap is a research lead, not corroboration. This run does not create or publish a video.",
        "", "## Feed status", "",
    ]
    for result in feed_results:
        lines.append(f"- **{result['name']}**: {result['status']} — {result['items_found']} items")
    if errors:
        lines.extend(["", "## Feed errors", ""])
        lines.extend(f"- {error}" for error in errors)
    lines.extend(["", "## Candidate headlines", ""])
    for item in items[:30]:
        date = item.get("published_at") or "date not parsed"
        lines.append(f"- [{item['title']}]({item['url']}) — {item['source_name']} — {date}")
        if item.get("summary"):
            lines.append(f"  - {item['summary'][:300]}")
    lines.extend(["", "## Related candidates (not verified)", ""])
    for pair in report["related_candidates"]:
        terms = ", ".join(pair["shared_discovery_terms"])
        lines.append(f"- [{pair['source_a_title']}]({pair['source_a_url']}) + [{pair['source_b_title']}]({pair['source_b_url']}); shared terms: {terms}")
    (OUTPUT_DIR / "research-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not items:
        raise RuntimeError("No approved-source items collected. Fail closed; no content may be published.")
    return report


if __name__ == "__main__":
    try:
        result = run_research()
        print(json.dumps({
            "status": "research_completed",
            "candidate_count": result["candidate_count"],
            "related_candidates": len(result["related_candidates"]),
            "feed_results": result["feed_results"],
            "errors": result["errors"],
            "publish_authorized": False,
        }, indent=2))
    except Exception as exc:
        print(f"RESEARCH FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
