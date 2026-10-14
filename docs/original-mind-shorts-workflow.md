# Recode Mind — original YouTube Shorts workflow

This is a new-channel editorial profile inspired only by broad short-form storytelling patterns. It is not a clone of another creator's scripts, visuals, music, branding, or watermark. The linked Instagram account's posts have not been independently inspected by this repository workflow, so no account-specific style claims are made.

## Phone/browser-only workflow (₹0)

1. Create the new YouTube channel in the YouTube app or browser. Use the channel name **Recode Mind** only if it is available and you want it; this repository cannot create a channel on your behalf.
2. Use the profile in `config/original_mind_channel.json` as the editorial contract.
3. Choose one narrow topic (attention, habits, memory, decision-making, or sleep). Do not diagnose viewers or make sensational claims about dopamine, trauma, or the brain.
4. Research the original source pages on APA, NIH/PubMed/PMC, or NHS. Record each claim, exact supporting passage, source URL, publication date, and limitations. RSS titles or search snippets alone are not evidence.
5. Write a fresh 75–130 word English script. Use a 0–2 second hook, one clear question, evidence-led explanation, a practical takeaway, and a short ending. Do not paraphrase a specific Reel line-by-line.
6. Create original graphics and narration. Do not download Recode Mind's inspiration account's video/audio, use its watermark, or reuse music without a license.
7. Export a 1080×1920 MP4 at 30 fps, H.264 video and AAC audio. Confirm duration is 30–60 seconds, both streams exist, audio is audible, captions are readable on a phone, and no third-party media appears without documented rights.
8. Review the factual claims and source notes manually. A source citation is not a copyright license; free-to-view does not mean free-to-reuse.
9. Upload as **Private** first in YouTube Studio. Inspect the video, metadata, and any copyright checks before deciding whether to publish publicly.

## Fail-closed rule

Do not publish if any source is missing, a factual claim is unsupported, rights are uncertain, rendering/metadata checks fail, or the final MP4 has not been inspected. Automatic public upload is intentionally disabled by default.

## Current implementation boundary

The added GitHub Actions job validates this channel profile and its policy tests only. It does **not** yet generate a Recode Mind MP4, verify a live Instagram account, create a YouTube channel, or upload/publish a video. The existing WhySpark NASA/NOAA pipeline is a separate science/technology workflow and must not be mistaken for this psychology-channel pipeline.
