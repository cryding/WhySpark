"""Upload a validated WhySpark Short to YouTube using OAuth refresh-token secrets.

No upload occurs unless PUBLISH_ENABLED=true and every supplied validation gate
passes. A successful upload is not considered complete until YouTube processing
reports succeeded and the returned privacy status matches the requested public
visibility.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

from src.publish_gate import evaluate_publish_gate

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
EPISODE_PATH = ARTIFACTS / "episode.json"
RENDER_REPORT_PATH = ARTIFACTS / "render-report.json"
RESEARCH_PATH = ARTIFACTS / "research.json"
UPLOAD_HISTORY_PATH = ARTIFACTS / "upload-history.json"


def required_secret(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required GitHub Actions secret is missing: {name}")
    return value


def refresh_credentials():
    client_id = required_secret("YOUTUBE_CLIENT_ID")
    client_secret = required_secret("YOUTUBE_CLIENT_SECRET")
    refresh_token = required_secret("YOUTUBE_REFRESH_TOKEN")
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("OAuth refresh did not return an access token.")
    return Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
    )


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise RuntimeError(f"Required validation artifact is missing: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    if os.environ.get("PUBLISH_ENABLED", "").lower() != "true":
        raise RuntimeError("PUBLISH_ENABLED is not true; public upload is disabled.")
    episode = load_json(EPISODE_PATH)
    render = load_json(RENDER_REPORT_PATH)
    research = load_json(RESEARCH_PATH)
    rights = render.get("rights", {})
    metadata = episode.get("metadata", {})
    gate = evaluate_publish_gate(research, rights, metadata, render)
    if not gate["passed"]:
        raise RuntimeError("Publishing blocked by safety gates: " + json.dumps(gate["errors"], ensure_ascii=False))

    history = load_json(UPLOAD_HISTORY_PATH) if UPLOAD_HISTORY_PATH.exists() else {"uploaded_hashes": [], "videos": []}
    digest = render.get("content_sha256", "")
    if digest in history.get("uploaded_hashes", []):
        raise RuntimeError("Duplicate video hash detected in persistent upload history.")

    credentials = refresh_credentials()
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    video_path = Path(render["video_path"])
    if not video_path.is_file():
        raise RuntimeError("Validated video file is missing.")
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": metadata["title"],
                "description": metadata["description"],
                "tags": metadata["tags"],
                "categoryId": str(metadata["category_id"]),
                "defaultLanguage": metadata["language"],
            },
            "status": {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": False,
            },
        },
        media_body=MediaFileUpload(str(video_path), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True),
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
    video_id = response.get("id")
    if not video_id:
        raise RuntimeError("YouTube API returned no video ID.")
    if response.get("status", {}).get("privacyStatus") != "private":
        raise RuntimeError(
            "YouTube did not confirm the initial private upload. Do not attempt public release."
        )

    processing = None
    deadline = time.time() + 600
    while time.time() < deadline:
        info = youtube.videos().list(part="processingDetails,status", id=video_id).execute()
        items = info.get("items", [])
        if not items:
            raise RuntimeError("Uploaded video disappeared from YouTube API lookup.")
        item = items[0]
        processing = item.get("processingDetails", {}).get("processingStatus", "")
        if processing == "succeeded":
            break
        if processing in {"failed", "terminated"}:
            raise RuntimeError(f"YouTube processing failed: {processing}")
        time.sleep(15)
    if processing != "succeeded":
        raise RuntimeError("YouTube processing was not confirmed within 10 minutes; video remains private.")

    # Public visibility is the final step: only after all gates and YouTube processing pass.
    youtube.videos().update(
        part="status",
        body={"id": video_id, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}},
    ).execute()
    visibility_check = youtube.videos().list(part="status", id=video_id).execute()
    verified_items = visibility_check.get("items", [])
    if not verified_items or verified_items[0].get("status", {}).get("privacyStatus") != "public":
        raise RuntimeError(
            "Public visibility could not be confirmed. The video may remain private; inspect YouTube Studio."
        )

    history.setdefault("uploaded_hashes", []).append(digest)
    history.setdefault("videos", []).append({
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "sha256": digest,
        "title": metadata["title"],
        "privacy_status": "public",
        "processing_status": "succeeded",
    })
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    UPLOAD_HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "published_and_processed", "video_id": video_id,
                      "url": f"https://www.youtube.com/watch?v={video_id}", "sha256": digest}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"PUBLISH BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
