# WhySpark — zero-budget YouTube automation

**Big Questions. Simple Answers.**

WhySpark is a phone-manageable, GitHub Actions-based science and technology video pipeline. It is designed for a ₹0 budget: no paid AI APIs, paid credits, or paid billing are required. The workflow runs on standard GitHub-hosted runners in this public repository.

## Current status

Implemented in this repository: an official-source RSS research collector, a daily GitHub Actions research workflow, and fail-closed publishing validation with regression tests. The research workflow writes a JSON/Markdown candidate report artifact. It does **not** yet generate a finished video or upload anything to YouTube. Do not treat this repository as a finished or connected YouTube publisher until script generation, semantic verification, original visuals, narration, rendering, OAuth secrets, and an end-to-end upload have all been implemented and tested.

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

The workflow `.github/workflows/daily-research.yml` runs at 14:30 UTC each day and can also be started from **Actions → WhySpark Daily Research → Run workflow**. It saves a JSON and Markdown research report as a GitHub Actions artifact for seven days. The workflow uses no AI API and has no YouTube publishing credentials. GitHub Actions status must be checked in the Actions tab; a committed workflow is not proof that a run succeeded.

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