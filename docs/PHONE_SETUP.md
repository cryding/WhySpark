# WhySpark setup from a phone browser

No terminal is required for the user. Open the repository at https://github.com/cryding/WhySpark.

## 1. Run a no-upload production test first

1. Open **Actions**.
2. Select **WhySpark Daily Production**.
3. Tap **Run workflow** and choose `main`.
4. Keep the repository variable `PUBLISH_ENABLED` unset. This allows research, script drafting, local claim checks, rendering, and artifact creation without uploading to YouTube.
5. Open the run. Wait for completion and inspect the step logs.
6. Download the `whyspark-production-...` artifact and check the generated MP4, source list, script, and render report.

A failed run must not be treated as ready. Fix the failure before enabling upload.

## 2. Configure YouTube API access

1. Open https://console.cloud.google.com/ in your phone browser and create/select a Google Cloud project.
2. Enable **YouTube Data API v3** in **APIs & Services → Library**.
3. Configure the OAuth consent screen and add your own Google account as a test user if using Testing mode.
4. Create OAuth client credentials and authorize the YouTube account that owns the channel.
5. The refresh token must include this scope: `https://www.googleapis.com/auth/youtube.force-ssl`. This is needed because WhySpark uploads privately and only changes the video to public after successful processing.
6. Keep the client secret and refresh token private. Never paste them into a chat, issue, source file, or workflow log.

**Important Google limitations:** OAuth consent projects in Testing mode expire authorizations after seven days for scopes beyond basic profile/email. For reliable scheduled use, configure the OAuth app appropriately for production and complete any verification Google requires. Separately, YouTube API projects created after 28 July 2020 may have uploads restricted to private visibility until the API project passes Google's audit. If that restriction applies, WhySpark must leave the upload private; it must not claim public publishing succeeded.

## 3. Save credentials as GitHub Actions secrets

In the repository, open **Settings → Secrets and variables → Actions → New repository secret** and add:

- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

Do not add the actual values to this document.

## 4. Enable automatic publishing

Only after a successful manual no-upload run and after you have reviewed the generated video:

1. Open **Settings → Secrets and variables → Actions → Variables**.
2. Add repository variable `PUBLISH_ENABLED` with value `true`.
3. Run **Actions → WhySpark Daily Production → Run workflow** once and inspect its logs.

The uploader runs the factual/source, media-rights, metadata, rendering, hash, and duplicate gates. It uploads privately, checks YouTube processing/rejection status, then requests public visibility and confirms it via the API. Any failed or unverified step blocks public release. If YouTube restricts public uploads, the video remains private and the run reports failure.

## Zero-budget guarantee

The workflow uses GitHub-hosted runners, public RSS feeds, freely downloadable open-source model weights, Pillow, espeak-ng, FFmpeg, and the YouTube Data API. No paid AI API, paid model endpoint, credit purchase, or paid billing is configured. Model downloads consume runner time and bandwidth but are not paid API calls.
