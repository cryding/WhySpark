# Implementation status

Last updated: 2026-10-13

## Implemented in `main`

- [x] Public repository `cryding/WhySpark` is the project home.
- [x] Official-source RSS research collector: `src/research.py`.
- [x] Source allowlist: NASA News Releases and NOAA National Ocean Service News in `config/sources.json`.
- [x] Research report output: `artifacts/research.json` and `artifacts/research-report.md`.
- [x] Daily GitHub Actions research workflow at 14:30 UTC: `.github/workflows/daily-research.yml`.
- [x] Research artifacts retained for seven days.
- [x] Fail-closed publishing validation for approved sources, independent-source coverage, claim evidence, semantic-verification records, original media rights, metadata, video streams/dimensions/duration, content hashes, and duplicate blocking: `src/publish_gate.py`.
- [x] Regression tests for research parsing and safety gates.
- [x] CI workflow configured for pushes, pull requests, and manual runs.

## Not implemented / not verified yet

- [ ] Actual script generation from verified evidence.
- [ ] Integrated semantic fact-checking model or verifier. A claim without a valid semantic-verification record is blocked.
- [ ] Original visual generation and local text-to-speech.
- [ ] FFmpeg rendering and independent ffprobe validation wired into the pipeline.
- [ ] YouTube OAuth credential setup and token refresh.
- [ ] Upload, post-upload processing verification, and idempotent publication history integrated end to end.
- [ ] End-to-end video generated and uploaded.
- [ ] Public publishing tested on the real WhySpark channel.
- [ ] Successful GitHub Actions run confirmed by inspecting run logs.

## Safety state

**Public publishing is not active.** The current daily workflow only collects research candidates and produces an artifact. It does not access YouTube credentials or upload videos. The validation module is a safety component, not an end-to-end publisher.

The repository is designed to fail closed. Keyword overlap is only a discovery signal and must never be treated as proof of factual corroboration. Do not add paid APIs, paid credits, or paid billing.
