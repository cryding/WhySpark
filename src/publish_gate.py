"""Fail-closed validation gates for WhySpark.

Lexical matching does not prove semantic truth. A claim must carry explicit
source evidence and a separate semantic-verification result. Uncertain or
absent data blocks publishing.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

APPROVED_HOSTS = {"nasa.gov", "www.nasa.gov", "noaa.gov", "www.noaa.gov", "oceanservice.noaa.gov"}
REQUIRED_RIGHTS_FIELDS = ("origin", "rights_status", "creator", "license")
ALLOWED_SEMANTIC_VERIFIERS = {"independent_entailment_model", "human_review"}


def _tokens(text: str) -> set[str]:
    stopwords = {
        "about", "after", "also", "been", "from", "have", "into", "more",
        "over", "than", "that", "their", "there", "these", "they", "this",
        "with", "will", "would", "your", "what", "when", "where", "which",
        "while", "were", "such", "some", "only", "because", "could",
    }
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]{3,}", text or "")
        if token.lower() not in stopwords
    }


def validate_research(research: dict, minimum_sources: int = 2) -> list[str]:
    errors: list[str] = []
    sources = research.get("sources")
    claims = research.get("claims")
    if not isinstance(sources, list) or len(sources) < minimum_sources:
        errors.append(f"Need at least {minimum_sources} independent sources.")
        sources = sources if isinstance(sources, list) else []
    unique_hosts: set[str] = set()
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"Source {index + 1} is malformed.")
            continue
        url = str(source.get("url", ""))
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or host not in APPROVED_HOSTS:
            errors.append(f"Source {index + 1} is not an approved HTTPS source.")
        if not source.get("title") or not source.get("published_at"):
            errors.append(f"Source {index + 1} is missing title or publication date.")
        if not str(source.get("evidence_text", "")).strip():
            errors.append(f"Source {index + 1} has no retained evidence text.")
        source_id = str(source.get("id", ""))
        if not source_id or source_id in source_ids:
            errors.append(f"Source {index + 1} has a missing or duplicate ID.")
        source_ids.add(source_id)
        if host:
            unique_hosts.add(host.removeprefix("www."))
    if len(unique_hosts) < minimum_sources:
        errors.append("Sources are not independent across the required number of approved hosts.")

    if not isinstance(claims, list) or not claims:
        errors.append("No factual claims were provided.")
        claims = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict) or not str(claim.get("text", "")).strip():
            errors.append(f"Claim {index + 1} is missing text.")
            continue
        verification = claim.get("semantic_verification")
        if not isinstance(verification, dict):
            errors.append(f"Claim {index + 1} has no semantic verification record.")
        else:
            if verification.get("status") != "pass":
                errors.append(f"Claim {index + 1} semantic verification did not pass.")
            if verification.get("method") not in ALLOWED_SEMANTIC_VERIFIERS:
                errors.append(f"Claim {index + 1} uses an unapproved semantic verification method.")
            confidence = verification.get("confidence")
            if not isinstance(confidence, (int, float)) or confidence < 0.90 or confidence > 1:
                errors.append(f"Claim {index + 1} semantic confidence must be between 0.90 and 1.00.")
        evidence_ids = claim.get("evidence_source_ids")
        if not isinstance(evidence_ids, list) or len(set(evidence_ids)) < minimum_sources:
            errors.append(f"Claim {index + 1} needs evidence IDs from at least {minimum_sources} sources.")
            continue
        matched = [source for source in sources if source.get("id") in evidence_ids]
        matched_hosts = {
            (urlparse(str(source.get("url", ""))).hostname or "").removeprefix("www.")
            for source in matched
        }
        if len(matched_hosts) < minimum_sources:
            errors.append(f"Claim {index + 1} lacks independent source-host coverage.")
            continue
        if isinstance(verification, dict):
            checked_ids = verification.get("checked_source_ids")
            if not isinstance(checked_ids, list) or not set(evidence_ids).issubset(set(checked_ids)):
                errors.append(f"Claim {index + 1} semantic verifier did not check every cited source.")
        claim_tokens = _tokens(str(claim.get("text", "")))
        if len(claim_tokens) < 3:
            errors.append(f"Claim {index + 1} is too short for evidence matching.")
            continue
        for source in matched:
            evidence_tokens = _tokens(str(source.get("evidence_text", "")))
            overlap = len(claim_tokens & evidence_tokens) / max(1, len(claim_tokens))
            if overlap < 0.60:
                errors.append(
                    f"Claim {index + 1} does not meet the conservative text-evidence threshold "
                    f"for source {source.get('id')} (overlap {overlap:.2f})."
                )
    return errors


def validate_rights(rights: dict) -> list[str]:
    errors: list[str] = []
    assets = rights.get("assets")
    if not isinstance(assets, list) or not assets:
        return ["No media rights inventory supplied."]
    for index, asset in enumerate(assets):
        if not isinstance(asset, dict):
            errors.append(f"Asset {index + 1} rights record is malformed.")
            continue
        for field in REQUIRED_RIGHTS_FIELDS:
            if not str(asset.get(field, "")).strip():
                errors.append(f"Asset {index + 1} is missing {field}.")
        if asset.get("rights_status") != "original_project_generated":
            errors.append(f"Asset {index + 1} is not verified as project-generated original media.")
        if asset.get("third_party_media") is not False:
            errors.append(f"Asset {index + 1} does not explicitly exclude third-party media.")
    return errors


def validate_metadata(metadata: dict) -> list[str]:
    errors: list[str] = []
    title = str(metadata.get("title", "")).strip()
    description = str(metadata.get("description", "")).strip()
    tags = metadata.get("tags")
    if not title or len(title) > 100:
        errors.append("Title must contain 1–100 characters.")
    if not description or len(description) > 5000:
        errors.append("Description must contain 1–5000 characters.")
    if not isinstance(tags, list) or not tags or any(
        not isinstance(tag, str) or not tag.strip() or len(tag) > 30 for tag in tags
    ):
        errors.append("Tags must be a non-empty list of non-blank strings no longer than 30 characters.")
    if not str(metadata.get("category_id", "")).isdigit():
        errors.append("A numeric YouTube category ID is required.")
    if metadata.get("language") != "en":
        errors.append("WhySpark's current pipeline requires English metadata (language=en).")
    if metadata.get("privacy_status") != "public":
        errors.append("Publishing metadata must explicitly request public status after all gates pass.")
    return errors


def validate_render(render: dict) -> list[str]:
    errors: list[str] = []
    video_path = Path(str(render.get("video_path", "")))
    if not video_path.is_file() or video_path.stat().st_size < 100_000:
        errors.append("Rendered video is missing or suspiciously small.")
    if not render.get("has_video_stream"):
        errors.append("Rendered file has no verified video stream.")
    if not render.get("has_audio_stream"):
        errors.append("Rendered file has no verified audio stream.")
    if render.get("width") != 1080 or render.get("height") != 1920:
        errors.append("Rendered Short must be exactly 1080x1920.")
    duration = render.get("duration_seconds")
    if not isinstance(duration, (int, float)) or not 15 <= duration <= 60:
        errors.append("Rendered Short duration must be 15–60 seconds.")
    if render.get("render_exit_code") != 0:
        errors.append("Renderer did not report a successful exit code.")
    content_hash = str(render.get("content_sha256", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", content_hash):
        errors.append("Rendered video is missing a valid SHA-256 content hash.")
    uploaded_hashes = render.get("uploaded_hashes", [])
    if not isinstance(uploaded_hashes, list):
        errors.append("Uploaded-content history is malformed.")
    elif content_hash in uploaded_hashes:
        errors.append("This exact video hash was already uploaded; duplicate publishing is blocked.")
    return errors


def content_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_publish_gate(research: dict, rights: dict, metadata: dict, render: dict,
                          minimum_sources: int = 2) -> dict:
    errors = []
    errors.extend(f"research: {error}" for error in validate_research(research, minimum_sources))
    errors.extend(f"rights: {error}" for error in validate_rights(rights))
    errors.extend(f"metadata: {error}" for error in validate_metadata(metadata))
    errors.extend(f"render: {error}" for error in validate_render(render))
    return {"passed": not errors, "errors": errors, "decision": "PUBLISH" if not errors else "BLOCK"}
