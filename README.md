# WhySpark — zero-budget YouTube automation

**Big Questions. Simple Answers.**

WhySpark is a phone-manageable, GitHub Actions-based science and technology video pipeline. It is designed for a ₹0 budget: no paid AI APIs, paid credits, or paid billing are required. The workflow runs on standard GitHub-hosted runners in this public repository.

## Current status

This repository is being built in stages. The safety gate and CI tests are the first stage; do not treat this repository as a finished or connected YouTube publisher until the production workflow, rendering, source verification, OAuth secrets, and an end-to-end upload have all been tested.

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

- Research: official/public source feeds and pages; sources are recorded in a provenance report.
- Script: generated from the collected evidence, not from a paid LLM.
- Visuals: original vector/diagram assets rendered locally.
- Narration: open-source local text-to-speech on the GitHub runner.
- Video: FFmpeg.
- Scheduling and execution: GitHub Actions.
- Publishing: YouTube Data API only after all gates pass.

No paid provider is configured by default. Do not add billing or paid API keys.

## GitHub setup (phone browser only)

1. Open **Settings → Secrets and variables → Actions** in this repository.
2. Add the required YouTube OAuth secrets only after the code and workflow are ready:
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`
3. Never put tokens in source files, issues, logs, or commit messages.
4. Open **Actions** to view tests and scheduled runs.
5. Do not enable automatic public upload until the full pipeline and YouTube channel connection have been verified.

YouTube OAuth credentials and API enablement are account-side setup requirements; GitHub cannot create these on your behalf. Some unverified YouTube API projects are restricted to private uploads until Google audits the API project.

## Local test command (optional)

The user does not need to run a terminal. GitHub Actions runs the tests automatically on pushes and pull requests.

## Status reporting

A passing unit test means only that the tested code paths passed. It does not mean a video was created, an upload occurred, or public publishing is enabled.