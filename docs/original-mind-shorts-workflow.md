# Recode Mind — phone-only Shorts production

## What runs automatically
The GitHub Actions workflow `Recode Mind Shorts — Research, Render and Verify` queries PubMed's public E-utilities for bibliographic metadata, writes a cautious research-literacy draft, renders original vector scenes and local espeak-ng narration, checks MP4 dimensions/codecs/duration/size, and stores a review artifact for seven days.

## Run it on Android
1. Open https://github.com/cryding/WhySpark/actions
2. Select **Recode Mind Shorts — Research, Render and Verify**.
3. Tap **Run workflow** and wait for the run to finish.
4. Open the completed run and download the artifact named `recode-mind-short-draft-...`.
5. Review the MP4 and research report before any upload.

## Non-negotiable publication hold
This pipeline does not publish to YouTube. It does not download or copy Instagram videos, scripts, music, or branding. The initial video is a research-literacy draft based on PubMed bibliographic metadata, not a summary of scientific findings. A human must open the full paper, review the wording, approve all claims, and inspect rights and audio before any public release. Passing FFmpeg checks proves file structure, not factual accuracy or copyright clearance.

## Zero-cost limits
GitHub-hosted runner availability and free usage quotas can change. No paid API, model credits, or paid billing are configured. If GitHub blocks the run because of account limits, the workflow stops rather than enabling billing.

## What is and is not verified
The source files are committed to GitHub, but a successful GitHub Actions run and a real MP4 artifact must be confirmed in the Actions UI. This repository edit alone is not evidence that the job ran successfully.
