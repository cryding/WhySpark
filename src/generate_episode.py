"""Generate a short script only from source candidates and locally verify every claim.

Uses free, downloadable open-source model weights on the GitHub runner; no paid
AI API or billing. If the models cannot load or any claim fails entailment,
the workflow stops before rendering/upload.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from src.publish_gate import APPROVED_HOSTS

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
RESEARCH_PATH = ARTIFACTS / "research.json"
EPISODE_PATH = ARTIFACTS / "episode.json"
GENERATOR_MODEL = "google/flan-t5-small"
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
MIN_ENTAILMENT_CONFIDENCE = 0.90


def load_models():
    # Model downloads are free; failures are fatal and must never be interpreted as a pass.
    writer = pipeline(
        "text2text-generation",
        model=GENERATOR_MODEL,
        tokenizer=GENERATOR_MODEL,
        device=-1,
    )
    tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL)
    verifier = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL)
    verifier.eval()
    return writer, tokenizer, verifier


def generate_claim(writer, title: str, summary: str) -> str:
    source_text = re.sub(r"\s+", " ", f"{title}. {summary}").strip()
    if len(source_text) < 50:
        raise RuntimeError("Source excerpt is too short for a factual script claim.")
    prompt = (
        "Write exactly one short, neutral factual sentence for a science education video. "
        "Use only facts explicitly stated in the source passage. Do not add numbers, causes, "
        "predictions, opinions, or background knowledge. Do not mention these instructions. "
        "Keep it under 24 words.\nSOURCE PASSAGE: " + source_text[:1800]
    )
    result = writer(prompt, max_new_tokens=48, do_sample=False, truncation=True)
    claim = re.sub(r"\s+", " ", result[0].get("generated_text", "")).strip().strip('"')
    words = claim.split()
    if len(words) < 6 or len(words) > 28:
        raise RuntimeError(f"Generated claim has unsafe/invalid length: {claim!r}")
    return claim


def entailment_score(tokenizer, model, premise: str, hypothesis: str) -> tuple[float, str]:
    inputs = tokenizer(
        premise, hypothesis, return_tensors="pt", truncation=True, max_length=512
    )
    with torch.no_grad():
        logits = model(**inputs).logits[0]
        probabilities = torch.softmax(logits, dim=-1).tolist()
    labels = model.config.id2label
    label_scores = {}
    for index, score in enumerate(probabilities):
        label = str(labels.get(index, labels.get(str(index), ""))).lower()
        label_scores[label] = float(score)
    entailment_labels = [label for label in label_scores if "entail" in label]
    if not entailment_labels:
        raise RuntimeError(
            "The downloaded NLI model does not expose a recognizable entailment label; blocking."
        )
    label = max(entailment_labels, key=lambda name: label_scores[name])
    return label_scores[label], label


def verify_claim(tokenizer, model, claim: str, source: dict) -> dict:
    premise = str(source.get("evidence_text", "")).strip()
    if not premise:
        return {"status": "fail", "reason": "No source evidence text"}
    confidence, label = entailment_score(tokenizer, model, premise, claim)
    passed = "entail" in label and confidence >= MIN_ENTAILMENT_CONFIDENCE
    return {
        "status": "pass" if passed else "fail",
        "method": "independent_entailment_model",
        "model": NLI_MODEL,
        "confidence": confidence,
        "label": label,
        "checked_source_ids": [source["id"]],
        "threshold": MIN_ENTAILMENT_CONFIDENCE,
    }


def main():
    if not RESEARCH_PATH.is_file():
        raise RuntimeError("Missing research.json. Run official-source research first.")
    report = json.loads(RESEARCH_PATH.read_text(encoding="utf-8"))
    items_by_url = {item.get("url"): item for item in report.get("items", [])}
    pairs = report.get("related_candidates", [])
    if not pairs:
        raise RuntimeError("No related official-source candidates found; no episode will be invented.")
    pair = None
    selected = []
    for candidate in pairs:
        left = items_by_url.get(candidate.get("source_a_url"))
        right = items_by_url.get(candidate.get("source_b_url"))
        if not left or not right:
            continue
        left_host = (urlparse(left.get("url", "")).hostname or "").lower()
        right_host = (urlparse(right.get("url", "")).hostname or "").lower()
        if left_host not in APPROVED_HOSTS or right_host not in APPROVED_HOSTS:
            continue
        if left_host.removeprefix("www.") == right_host.removeprefix("www."):
            continue
        if not left.get("published_at") or not right.get("published_at"):
            continue
        if len(left.get("summary", "")) < 50 or len(right.get("summary", "")) < 50:
            continue
        pair = candidate
        selected = [left, right]
        break
    if not pair:
        raise RuntimeError("No candidate pair meets approved-host, date, and evidence-text requirements.")

    writer, tokenizer, verifier = load_models()
    sources = []
    claims = []
    segments = [{
        "visual_title": "Big questions. Simple answers.",
        "narration": "Welcome to WhySpark. Let's explore two official science updates and check what their sources actually say."
    }]
    for index, item in enumerate(selected, start=1):
        source_id = f"source-{index}"
        source = {
            "id": source_id,
            "url": item["url"],
            "title": item["title"],
            "published_at": item["published_at"],
            "evidence_text": re.sub(r"\s+", " ", (item.get("title", "") + ". " + item.get("summary", ""))).strip(),
            "source_name": item["source_name"],
        }
        claim_text = generate_claim(writer, item["title"], item["summary"])
        verification = verify_claim(tokenizer, verifier, claim_text, source)
        if verification["status"] != "pass":
            raise RuntimeError(
                f"Claim failed local entailment verification ({verification['confidence']:.3f}, "
                f"{verification['label']}): {claim_text}"
            )
        sources.append(source)
        claims.append({
            "id": f"claim-{index}",
            "text": claim_text,
            "evidence_source_ids": [source_id],
            "semantic_verification": verification,
        })
        segments.append({
            "visual_title": f"Source {index}: {item['source_name']}",
            "narration": claim_text,
            "claim_id": f"claim-{index}",
        })

    segments.append({
        "visual_title": "Follow the evidence",
        "narration": "Read both source links in the description. Keep asking questions, and follow the evidence."
    })
    topic_words = pair.get("shared_discovery_terms", [])[:3]
    topic = " ".join(word.capitalize() for word in topic_words) or "Science Update"
    title = f"What Science Sources Report About {topic}"[:95]
    description = (
        "WhySpark — Big Questions. Simple Answers.\n\n"
        "This short summarizes claims checked against official source excerpts using a local natural-language-entailment model. "
        "Automated model checks are imperfect; consult the original sources.\n\n"
        + "\n".join(f"{source['source_name']}: {source['url']}" for source in sources)
        + "\n\nOriginal WhySpark vector visuals and locally generated narration."
    )
    episode = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generation_model": GENERATOR_MODEL,
        "verification_model": NLI_MODEL,
        "paid_services_used": False,
        "topic": topic,
        "segments": segments,
        "metadata": {
            "title": title,
            "description": description,
            "tags": ["WhySpark", "science", "technology", "education", "science news"],
            "category_id": "28",
            "language": "en",
            "privacy_status": "public",
        },
        "source_urls": [source["url"] for source in sources],
        "claims": claims,
        "publish_policy": "fail_closed",
    }
    report["sources"] = sources
    report["claims"] = claims
    report["verification"] = {
        "status": "pass",
        "model": NLI_MODEL,
        "threshold": MIN_ENTAILMENT_CONFIDENCE,
        "warning": "NLI is a fallible automated check, not a guarantee of truth; source links are included for audit.",
    }
    RESEARCH_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    EPISODE_PATH.write_text(json.dumps(episode, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "status": "episode_generated_and_claims_passed_nli",
        "topic": topic,
        "claims_verified": len(claims),
        "source_count": len(sources),
        "publish_authorized": False,
        "next_step": "Render and run every publishing gate before upload.",
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"EPISODE GENERATION BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
