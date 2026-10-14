"""Validate the new-channel profile without downloading or copying third-party content."""
from __future__ import annotations

import json
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1] / "config" / "original_mind_channel.json"
REQUIRED_DOMAINS = {"apa.org", "nih.gov", "pubmed.ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov", "nhs.uk"}


def validate(profile: dict) -> list[str]:
    errors = []
    if profile.get("channel_name") != "Recode Mind":
        errors.append("Unexpected channel name.")
    fmt = profile.get("format", {})
    if fmt.get("platform") != "YouTube Shorts":
        errors.append("Platform must be YouTube Shorts.")
    duration = fmt.get("target_duration_seconds")
    if duration != [30, 60]:
        errors.append("Target duration must be 30–60 seconds.")
    editorial = profile.get("editorial_rules", {})
    for key in (
        "inspiration_only",
        "require_human_review_before_publication",
        "publish_only_after_all_checks_pass",
    ):
        if editorial.get(key) is not True:
            errors.append(f"{key} must be true.")
    for key in (
        "copy_other_account_scripts",
        "download_or_reuse_other_account_media",
        "imitate_branding_or_watermarks",
        "medical_or_psychological_diagnosis",
        "unsupported_neuroscience_claims",
    ):
        if editorial.get(key) is not False:
            errors.append(f"{key} must be false.")
    domains = set(editorial.get("required_source_domains", []))
    if not REQUIRED_DOMAINS.issubset(domains):
        errors.append("Required reputable psychology/health source allowlist is incomplete.")
    constraints = profile.get("production_constraints", {})
    if constraints.get("budget_inr") != 0:
        errors.append("Budget must remain ₹0.")
    if constraints.get("terminal_required") is not False:
        errors.append("Phone/browser workflow must not require a terminal.")
    if constraints.get("paid_apis_or_credits") is not False:
        errors.append("Paid APIs/credits must remain disabled.")
    if constraints.get("automatic_public_upload_enabled") is not False:
        errors.append("Public auto-upload must remain disabled until the production pipeline is verified.")
    return errors


def main() -> None:
    if not PROFILE.is_file():
        raise SystemExit("BLOCK: channel profile is missing.")
    try:
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"BLOCK: channel profile cannot be read: {exc}") from exc
    errors = validate(profile)
    if errors:
        raise SystemExit("BLOCK: " + "; ".join(errors))
    print("PASS: original-channel profile and fail-closed publication policy validated.")
    print("NOTE: this preflight does not prove factual accuracy, copyright clearance, MP4 rendering, or YouTube upload readiness.")


if __name__ == "__main__":
    main()
