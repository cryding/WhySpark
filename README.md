# WhySpark — zero-budget YouTube automation

**Big Questions. Simple Answers.**

WhySpark is a phone-manageable, GitHub Actions-based science and technology video pipeline. It is designed for a ₹0 budget: no paid AI APIs, paid credits, or paid billing are required. The workflow runs on standard GitHub-hosted runners in this public repository.

## Current status

Implemented in code: official-source RSS discovery, local model-based script drafting and natural-language-entailment checks, original vector visuals, local espeak-ng narration, FFmpeg rendering, fail-closed publication gates, and a YouTube OAuth uploader that uploads privately first and switches to public only after processing succeeds. A daily GitHub Actions workflow connects these stages. **The complete end-to-end workflow has not yet been verified by a successful Actions run or a real channel upload.** Model checks are fallible and do not guarantee truth or copyright clearance.

## Safety contract

The publisher must stop unless every required check passes:

- Every factual claim is mapped to evidence from approved sources; insufficient or ambiguous evidence fails closed.
- Media is created by this project (vector visuals and local TTS); third-party media is not downloaded into videos.
- The rendered file is non-empty, has expected dimensions, has a video stream and an audio stream, and passes the configured duration/codec checks.
- Title, description, tags, category, and language pass metadata validation.
- The video content hash has not already been uploaded.
- YouTube processing is checked after upload. A failed or unverified upload is never marked successful.

Automated checks cannot prove semantic truth or guarantee that YouTube will not later issue a Content ID claim. When the system cannot establish a check, it must stop rather than guess.

## Zero-cost design

- Research: official NASA and NOAA RSS feeds; candidate headlines and links are recorded in a provenance report. Keyword overlap is discovery only, never proof of factual corroboration.
- Script: generated from the collected evidence, not from a paid LLM.
- Visuals: original vector/diagram assets rendered locally.
- Narration: open-source local text-to-speech on the GitHub runner.
- Video: FFmpeg.
- Scheduling and execution: GitHub Actions.
- Publishing: YouTube Data API only after all gates pass.

No paid provider is configured by default. Do not add billing or paid API keys.

## Daily research automation

The workflow `.github/workflows/daily-research.yml` runs at 14:30 UTC (8:00 PM India time) and can also be started from **Actions → WhySpark Daily Production → Run workflow**. It downloads free CPU model weights, discovers official-source topics, drafts a script, checks each claim with a local entailment model, renders original visuals and local narration, and stores run artifacts for seven days. No paid API or billing is configured. A passing model score is not a guarantee of truth.

## GitHub setup (phone browser only)

1. Open **Settings → Secrets and variables → Actions** in this repository.
2. Add these GitHub Actions secrets after setting up OAuth in Google Cloud: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN`.
3. Under **Variables**, add `PUBLISH_ENABLED` with value `true` only when you are ready to permit automatic public release. Leave it unset/false to generate artifacts without uploading.
4. Never put tokens in source files, issues, logs, or commit messages.
5. Open **Actions → WhySpark Daily Production → Run workflow** and inspect the run and artifacts before enabling publishing.
6. The uploader keeps the video private until the API reports successful processing; it then requests public visibility and verifies the status. If any check fails, it stops.

YouTube OAuth credentials and API enablement are account-side setup requirements; GitHub cannot create these on your behalf. Some YouTube API projects created after 28 July 2020 are restricted to private uploads until Google audits the API project. This pipeline will not claim public publishing succeeded if YouTube refuses the final visibility change.

## Local test command (optional)

The user does not need to run a terminal. GitHub Actions runs the tests automatically on pushes and pull requests.

## Status reporting

A passing unit test means only that the tested code paths passed. It does not mean a video was created, an upload occurred, or public publishing is enabled.