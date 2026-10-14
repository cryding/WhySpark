"""Render WhySpark Shorts with HyperFrames in a free GitHub Actions runner.

This is a separate, opt-in rendering path; it never publishes to YouTube.
Uses project-generated graphics and local espeak-ng narration only.
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
EPISODE = ARTIFACTS / "episode.json"
WORK = ARTIFACTS / "hyperframes"
OUTPUT = ARTIFACTS / "whyspark-short.mp4"


def run(command: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout[-2000:]}\n{result.stderr[-3000:]}"
        )
    return result.stdout


def probe_duration(path: Path) -> float:
    raw = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ]).strip()
    value = float(raw)
    if value <= 0:
        raise RuntimeError(f"Invalid audio duration: {path}")
    return value


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_html(segments: list[dict], durations: list[float]) -> str:
    start_times = []
    cursor = 0.0
    for duration in durations:
        start_times.append(cursor)
        cursor += duration
    total = cursor
    scene_markup = []
    timeline_items = []
    for index, (segment, start, duration) in enumerate(zip(segments, start_times, durations)):
        title = esc(segment["visual_title"])
        narration = esc(segment["narration"])
        scene_id = f"scene-{index}"
        scene_markup.append(f"""
<section id="{scene_id}" class="clip scene" data-start="{start:.3f}"
 data-duration="{duration:.3f}" data-track-index="1">
  <div class="nebula nebula-a"></div><div class="nebula nebula-b"></div>
  <div class="grid"></div>
  <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
  <div class="core"><div class="core-ring"></div><div class="core-dot"></div>
    <span class="particle p1"></span><span class="particle p2"></span>
    <span class="particle p3"></span><span class="particle p4"></span>
  </div>
  <div class="brand">WHYSPARK <span>•</span> BIG QUESTIONS. SIMPLE ANSWERS.</div>
  <div class="eyebrow">SCIENCE / EXPLAINED</div>
  <h1 id="title-{index}">{title}</h1>
  <p id="copy-{index}" class="copy">{narration}</p>
  <div class="progress"><i id="progress-{index}"></i></div>
  <div class="footer"><span>FOLLOW THE EVIDENCE</span><span>{index + 1:02d} / {len(segments):02d}</span></div>
</section>
""")
        timeline_items.append(
            f'tl.from("#title-{index}", {{ opacity: 0, y: 70, scale: 0.96, duration: 0.65, ease: "power3.out" }}, {start:.3});'
            f'tl.from("#copy-{index}", {{ opacity: 0, y: 28, duration: 0.55 }}, {start + 0.75:.3});'
            f'tl.from("#progress-{index}", {{ scaleX: 0, transformOrigin: "left center", duration: {max(0.3, duration - 0.4):.3}, ease: "none" }}, {start:.3});'
            f'tl.from("#{scene_id} .core", {{ opacity: 0, scale: 0.65, duration: 0.8 }}, {start:.3});'
        )
    audio_markup = []
    for index, (start, duration) in enumerate(zip(start_times, durations)):
        audio_markup.append(
            f'<audio id="voice-{index}" data-start="{start:.3f}" '
            f'data-duration="{duration:.3f}" data-track-index="0" '
            f'src="./voice-{index:02d}.wav"></audio>'
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WhySpark — Cinematic Science Short</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#050816;color:#fff;font-family:Arial,Helvetica,sans-serif}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:radial-gradient(ellipse at 50% 40%,#101e46 0%,#080d22 48%,#03050d 100%)}}
.scene{{position:absolute;inset:0;width:1080px;height:1920px;overflow:hidden;background:radial-gradient(ellipse at 50% 40%,rgba(20,57,115,.56),rgba(3,5,14,.97) 67%);color:#f8fbff}}
.nebula{{position:absolute;width:760px;height:760px;border-radius:50%;filter:blur(80px);opacity:.24}}
.nebula-a{{background:#007bff;left:-260px;top:280px}}.nebula-b{{background:#00e5d4;right:-350px;top:650px}}
.grid{{position:absolute;inset:0;opacity:.11;background-image:linear-gradient(rgba(100,180,255,.22) 1px,transparent 1px),linear-gradient(90deg,rgba(100,180,255,.22) 1px,transparent 1px);background-size:66px 66px;mask-image:linear-gradient(transparent,black 22%,black 75%,transparent)}}
.brand{{position:absolute;left:70px;right:70px;top:85px;font-size:23px;letter-spacing:3px;font-weight:800;color:#eaf3ff}}.brand span{{color:#00e5d4}}
.eyebrow{{position:absolute;left:72px;top:760px;color:#00e5d4;letter-spacing:7px;font-size:20px;font-weight:700}}
h1{{position:absolute;left:70px;right:70px;top:820px;margin:0;font-size:68px;line-height:1.08;font-weight:800;letter-spacing:-2px;text-shadow:0 0 28px rgba(0,145,255,.22)}}
.copy{{position:absolute;left:74px;right:74px;top:1110px;font-size:34px;line-height:1.42;color:#cbd9ef;margin:0;max-height:330px;overflow:hidden}}
.core{{position:absolute;width:500px;height:500px;left:290px;top:210px;border-radius:50%;display:grid;place-items:center;filter:drop-shadow(0 0 42px rgba(0,206,255,.35))}}
.core-ring{{position:absolute;inset:30px;border:2px solid rgba(0,229,212,.7);border-radius:50%;box-shadow:0 0 35px rgba(0,229,212,.2),inset 0 0 35px rgba(0,229,212,.12)}}
.core:before,.core:after{{content:"";position:absolute;border:1px solid rgba(78,155,255,.7);border-radius:50%;width:440px;height:190px;transform:rotate(32deg)}}
.core:after{{transform:rotate(-32deg);width:190px;height:440px}}
.core-dot{{width:96px;height:96px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff,#00e5d4 38%,#0067ff 72%);box-shadow:0 0 60px #008cff,0 0 110px rgba(0,229,212,.5)}}
.particle{{position:absolute;width:18px;height:18px;border-radius:50%;background:#fff;box-shadow:0 0 22px #00e5d4}}
.p1{{top:54px;left:242px}}.p2{{top:245px;right:34px}}.p3{{bottom:45px;left:120px}}.p4{{top:145px;right:85px}}
.orbit{{position:absolute;border:1px solid rgba(0,229,212,.18);border-radius:50%;width:790px;height:790px;left:145px;top:60px}}
.orbit-two{{width:930px;height:930px;left:75px;top:-10px;border-color:rgba(78,155,255,.12)}}
.progress{{position:absolute;left:72px;right:72px;bottom:180px;height:4px;background:rgba(255,255,255,.14);overflow:hidden}}.progress i{{display:block;height:100%;width:100%;background:linear-gradient(90deg,#007bff,#00e5d4)}}
.footer{{position:absolute;bottom:105px;left:72px;right:72px;display:flex;justify-content:space-between;font-size:18px;letter-spacing:3px;color:#8ea5c7}}
</style></head><body>
<div id="root" data-composition-id="whyspark-short" data-start="0" data-width="1080" data-height="1920">
{''.join(scene_markup)}
{''.join(audio_markup)}
<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
<script>
const tl = gsap.timeline({{paused:true}});
{''.join(timeline_items)}
window.__timelines = window.__timelines || {{}};
window.__timelines["whyspark-short"] = tl;
</script>
</div></body></html>"""


def main() -> None:
    if not EPISODE.is_file():
        raise RuntimeError("Missing artifacts/episode.json; research and claim checks must run first.")
    episode = json.loads(EPISODE.read_text(encoding="utf-8"))
    segments = episode.get("segments")
    if not isinstance(segments, list) or not 3 <= len(segments) <= 8:
        raise RuntimeError("Episode must contain 3–8 reviewed segments.")
    for i, segment in enumerate(segments):
        if not str(segment.get("narration", "")).strip() or not str(segment.get("visual_title", "")).strip():
            raise RuntimeError(f"Segment {i + 1} is missing narration or title.")
    for tool in ("node", "npm", "npx", "ffmpeg", "ffprobe", "espeak-ng"):
        if not shutil.which(tool):
            raise RuntimeError(f"Required free tool is missing: {tool}")
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    durations = []
    for index, segment in enumerate(segments):
        audio = WORK / f"voice-{index:02d}.wav"
        run(["espeak-ng", "-v", "en-us", "-s", "150", "-w", str(audio), str(segment["narration"])])
        durations.append(probe_duration(audio))
    total = sum(durations)
    if not 15 <= total <= 60:
        raise RuntimeError(f"Narration duration must be 15–60 seconds; got {total:.2f}s.")
    (WORK / "index.html").write_text(build_html(segments, durations), encoding="utf-8")
    # Structural validation before rendering; no YouTube upload occurs in this workflow.
    run(["npx", "--yes", "hyperframes", "lint"], cwd=WORK)
    run(["npx", "--yes", "hyperframes", "render", "--output", str(OUTPUT), "--fps", "30", "--quality", "standard"], cwd=WORK)
    details = json.loads(run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height:format=duration,size,format_name",
        "-of", "json", str(OUTPUT)
    ]))
    streams = details.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = details.get("format", {})
    duration = float(fmt.get("duration", 0))
    size = int(fmt.get("size", 0))
    if not video or not audio:
        raise RuntimeError("Final MP4 must contain both video and audio streams.")
    if (video.get("width"), video.get("height")) != (1080, 1920):
        raise RuntimeError(f"Unexpected video dimensions: {video.get('width')}x{video.get('height')}")
    if video.get("codec_name") != "h264" or audio.get("codec_name") != "aac" or "mp4" not in fmt.get("format_name", ""):
        raise RuntimeError("Final file did not pass MP4/H.264/AAC checks.")
    if not 15 <= duration <= 60 or size < 100_000:
        raise RuntimeError(f"Final file failed duration/size checks: {duration:.2f}s, {size} bytes")
    from src.publish_gate import content_sha256
    report = {
        "status": "rendered_and_verified",
        "renderer": "HyperFrames",
        "video_path": str(OUTPUT),
        "width": 1080, "height": 1920, "fps": 30,
        "duration_seconds": duration, "bytes": size,
        "video_codec": video["codec_name"], "audio_codec": audio["codec_name"],
        "container": fmt.get("format_name", ""),
        "content_sha256": content_sha256(OUTPUT),
        "third_party_media": False,
        "audio_source": "espeak-ng local TTS",
        "visual_source": "original HTML/CSS/GSAP graphics",
        "paid_services_used": False,
        "youtube_upload_attempted": False,
    }
    (ARTIFACTS / "render-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"HYPERFRAMES RENDER BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
