# Implementation status

Last updated: 2026-10-13

## Code present on `main`

- [x] Official-source RSS discovery from NASA and NOAA: `src/research.py`.
- [x] Candidate reports and topic overlap discovery.
- [x] Local script generation with `google/flan-t5-small`: `src/generate_episode.py`.
- [x] Local NLI claim check with `cross-encoder/nli-deberta-v3-small`, threshold 0.90; any failed claim blocks production.
- [x] Original Pillow-generated vector visuals, local `espeak-ng` narration, FFmpeg render and `ffprobe` checks: `src/render_short.py`.
- [x] Fail-closed validation for approved source hosts, independent source diversity, claim evidence and NLI records, original media rights records, metadata, render properties, hashes, and duplicates: `src/publish_gate.py`.
- [x] YouTube OAuth uploader: `src/youtube_upload.py`. It uploads privately, waits for YouTube processing to succeed, then requests public visibility and verifies it.
- [x] Persistent duplicate hash history: `state/upload-history.json`.
- [x] Daily workflow connects research → script and local NLI → render → gated upload: `.github/workflows/daily-research.yml`.
- [x] CI workflow and unit tests are present.
- [x] No paid AI API, credit purchase, or paid billing configured.

## Not yet verified

- [ ] Full GitHub Actions production workflow passes end to end.
- [ ] The model downloads and inference finish within the GitHub runner time/resource limits.
- [ ] Real source candidates meet the required independent-host and publication-date checks.
- [ ] YouTube OAuth secrets have been configured and refresh successfully.
- [ ] The first private upload processes successfully.
- [ ] The channel/API project is permitted to make uploads public.
- [ ] Public upload and duplicate-history persistence have passed a real run.

## Activation controls

Automatic upload runs only when the repository variable `PUBLISH_ENABLED` equals `true` and all three secrets are present:
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

Without the variable, the workflow should generate and retain artifacts without attempting upload. Do not set the variable until a manual production run has been reviewed.

## Safety limits

NLI is a probabilistic text entailment check, not a guarantee of factual truth. The pipeline cites the official sources in the description and stops on model/source failures, but no automated tool can guarantee that a source is correct or that a platform will never raise a copyright claim. Source media is not downloaded; the video uses project-generated vector art and local TTS.

A code commit is not proof of a successful deployment, render, or upload. Do not report those as completed until the GitHub Actions run and YouTube status have been verified.
