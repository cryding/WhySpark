"""Prepare a cautious, source-linked original-mind Short draft from PubMed metadata.

This is a draft generator, not an automated scientific fact-checker. It uses
study titles and public bibliographic metadata, not copied article abstracts.
Public publishing remains disabled; human review is required.
"""
from __future__ import annotations
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
QUERY = '(psychology[Title/Abstract] OR attention[Title/Abstract] OR memory[Title/Abstract] OR behavior[Title/Abstract] OR sleep[Title/Abstract]) AND humans[MeSH Terms]'


def get_json(url: str, params: dict) -> dict:
    response = requests.get(url, params=params, timeout=30, headers={"User-Agent":"RecodeMindZeroBudget/1.0"})
    response.raise_for_status()
    return response.json()


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    search = get_json(BASE + "esearch.fcgi", {"db":"pubmed","term":QUERY,"retmax":12,"sort":"date","retmode":"json"})
    ids = search.get("esearchresult", {}).get("idlist", [])
    if not ids:
        raise RuntimeError("No PubMed records returned; stopping instead of inventing a topic.")
    summary = get_json(BASE + "esummary.fcgi", {"db":"pubmed","id":",".join(ids[:12]),"retmode":"json"})
    records = summary.get("result", {})
    candidates = []
    for pmid in ids:
        record = records.get(pmid, {})
        title = re.sub(r"\s+", " ", str(record.get("title", ""))).strip().rstrip(".")
        if not title or title.lower() == "untitled":
            continue
        candidates.append({
            "pmid": pmid,
            "title": title,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "published": str(record.get("pubdate", "")),
            "journal": str(record.get("fulljournalname", record.get("source", ""))),
            "source_type": "PubMed bibliographic metadata",
            "evidence_limit": "Title and metadata only; does not establish study findings or causal claims."
        })
    if not candidates:
        raise RuntimeError("PubMed returned no usable titled records.")
    selected = candidates[0]
    title = selected["title"]
    # Script contains no assertion about the study's results. It frames the study
    # as a research question and explicitly tells viewers not to infer results
    # from a title alone.
    segments = [
        {"visual_title":"WHAT SHAPES THE MIND?", "narration":"What shapes the way we think, focus, and behave? A good answer starts with evidence, not a viral claim."},
        {"visual_title":"A REAL RESEARCH QUESTION", "narration":"A published paper listed on PubMed is titled: " + title + ". Its title tells us the topic researchers examined, not what they proved."},
        {"visual_title":"CHECK THE EVIDENCE", "narration":"Open the study, check its methods and limitations, and avoid turning one paper into a universal rule. Follow for careful psychology, without the hype."}
    ]
    episode = {
        "channel":"Recode Mind",
        "draft_status":"human_review_required",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "segments":segments,
        "metadata":{
            "title":"What Shapes the Mind? | Research Without the Hype #Shorts",
            "description":"A research-literacy Short. Featured record: " + selected["url"] + "\nThis draft uses bibliographic metadata only; it does not claim the study's results. Check the full paper and limitations before relying on any finding.\n#Psychology #Research #Shorts",
            "tags":["psychology","research literacy","human behavior","science","shorts"],
            "category_id":"27",
            "language":"en"
        },
        "research_records":[selected],
        "review_checklist":{
            "full_text_reviewed":False,
            "claims_independently_verified":False,
            "human_approval":False,
            "copyright_review":False,
            "approved_for_publication":False
        },
        "publication_policy":"PRIVATE_DRAFT_ONLY",
        "uploaded_hashes":[]
    }
    (ARTIFACTS/"research.json").write_text(json.dumps({"query":QUERY,"records":candidates,"selected":selected,"limitations":"Bibliographic metadata only; no result claims inferred."},indent=2),encoding="utf-8")
    (ARTIFACTS/"episode.json").write_text(json.dumps(episode,indent=2),encoding="utf-8")
    (ARTIFACTS/"research-report.md").write_text(
        "# Recode Mind research candidate\n\n"
        f"- **Title:** {selected['title']}\n- **Source:** {selected['url']}\n"
        f"- **Journal:** {selected['journal']}\n- **Date:** {selected['published']}\n\n"
        "## Limitations\nBibliographic metadata only. No results, causality, or clinical recommendations are asserted. A human must open and review the full record before publication.\n",
        encoding="utf-8")
    print(json.dumps({"status":"draft_created","selected":selected,"publication":"BLOCKED_PENDING_HUMAN_REVIEW","candidates":len(candidates)},indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RESEARCH BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
