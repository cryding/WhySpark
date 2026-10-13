"""Render a validated 15–60 second WhySpark Short using original graphics.

Requires a prepared artifacts/episode.json. This renderer does not create or
assert semantic verification; the publishing gate blocks missing verification.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
WORK = ARTIFACTS / "render_work"
EPISODE_PATH = ARTIFACTS / "episode.json"
VIDEO_PATH = ARTIFACTS / "whyspark-short.mp4"


def run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout[-1500:]}\n{result.stderr[-2500:]}"
        )


def load_font(size: int, bold: bool = False):
    candidates = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else []
    ) + [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def wrap_to_width(draw, text, font, max_width):
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def make_frame(title: str, narration: str, index: int, total: int, output: Path):
    width, height = 1080, 1920
    image = Image.new("RGB", (width, height), "#F7F4EC")
    draw = ImageDraw.Draw(image)
    ink, accent = "#14213D", "#007F86"
    draw.rectangle((0, 0, width, 24), fill=accent)
    draw.text((72, 72), "WHYSPARK  •  BIG QUESTIONS. SIMPLE ANSWERS.", fill=ink, font=load_font(27, True))
    draw.line((72, 135, width - 72, 135), fill="#D6D4CC", width=3)

    # Original, deterministic vector illustration: connected nodes and orbit rings.
    cx, cy = width // 2, 650
    draw.ellipse((cx - 235, cy - 235, cx + 235, cy + 235), outline=accent, width=8)
    draw.ellipse((cx - 165, cy - 165, cx + 165, cy + 165), outline="#B6D9D6", width=6)
    points = [(cx, cy - 170), (cx + 155, cy + 55), (cx - 150, cy + 80), (cx + 20, cy + 185)]
    for x, y in points:
        draw.line((cx, cy, x, y), fill=ink, width=5)
        draw.ellipse((x - 24, y - 24, x + 24, y + 24), fill=accent, outline=ink, width=3)
    draw.ellipse((cx - 34, cy - 34, cx + 34, cy + 34), fill=ink)

    title_font = load_font(54, True)
    body_font = load_font(38)
    y = 1010
    for line in wrap_to_width(draw, title, title_font, width - 144)[:4]:
        draw.text((72, y), line, fill=ink, font=title_font)
        y += 70
    y += 35
    for line in wrap_to_width(draw, narration, body_font, width - 144)[:6]:
        draw.text((72, y), line, fill="#344054", font=body_font)
        y += 54
    draw.line((72, 1695, width - 72, 1695), fill="#D6D4CC", width=3)
    draw.text((72, 1735), "Evidence-linked science • Original visuals", fill=ink, font=load_font(27))
    draw.text((width - 170, 1735), f"{index + 1:02d}/{total:02d}", fill=accent, font=load_font(27, True))
    image.save(output, format="PNG", optimize=True)


def main():
    if not EPISODE_PATH.is_file():
        raise RuntimeError("Missing artifacts/episode.json. Research candidates are not automatically publishable.")
    episode = json.loads(EPISODE_PATH.read_text(encoding="utf-8"))
    segments = episode.get("segments")
    if not isinstance(segments, list) or not 3 <= len(segments) <= 8:
        raise RuntimeError("Episode must contain 3–8 reviewed segments.")
    for index, segment in enumerate(segments):
        if not str(segment.get("narration", "")).strip() or not str(segment.get("visual_title", "")).strip():
            raise RuntimeError(f"Segment {index + 1} is missing narration or visual title.")

    for tool in ("ffmpeg", "ffprobe", "espeak-ng"):
        if not shutil.which(tool):
            raise RuntimeError(f"Required free tool is missing: {tool}")
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    concat_file = WORK / "concat.txt"
    concat_lines = []
    for index, segment in enumerate(segments):
        image_path = WORK / f"scene-{index:02d}.png"
        audio_path = WORK / f"scene-{index:02d}.wav"
        clip_path = WORK / f"scene-{index:02d}.mp4"
        make_frame(
            str(segment["visual_title"]),
            str(segment["narration"]),
            index,
            len(segments),
            image_path,
        )
        run(["espeak-ng", "-v", "en-us", "-s", "150", "-w", str(audio_path), str(segment["narration"])])
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True,
        )
        if probe.returncode or not probe.stdout.strip():
            raise RuntimeError(f"Could not verify narration duration for scene {index + 1}.")
        duration = float(probe.stdout.strip()) + 0.35
        run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(image_path), "-i", str(audio_path),
            "-t", f"{duration:.3f}", "-vf", "fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25",
            "-c:a", "aac", "-b:a", "128k", "-shortest", str(clip_path),
        ])
        concat_lines.append(f"file '{clip_path.as_posix()}'")
    concat_file.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(VIDEO_PATH),
    ])
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height:format=duration,size,format_name", "-of", "json", str(VIDEO_PATH)
    ], capture_output=True, text=True)
    if probe.returncode:
        raise RuntimeError("ffprobe could not inspect the final video.")
    details = json.loads(probe.stdout)
    streams = details.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    duration = float(details.get("format", {}).get("duration", 0))
    size = int(details.get("format", {}).get("size", 0))
    container = details.get("format", {}).get("format_name", "")
    if not video or not audio or video.get("width") != 1080 or video.get("height") != 1920:
        raise RuntimeError("Final render failed stream/dimension checks.")
    if video.get("codec_name") != "h264" or audio.get("codec_name") != "aac" or "mp4" not in container:
        raise RuntimeError("Final render failed MP4/H.264/AAC codec checks.")
    if not 15 <= duration <= 60 or size < 100_000:
        raise RuntimeError(f"Final render failed duration/size checks: duration={duration}, bytes={size}")
    from src.publish_gate import content_sha256
    result = {
        "video_path": str(VIDEO_PATH),
        "has_video_stream": True,
        "has_audio_stream": True,
        "width": int(video["width"]),
        "height": int(video["height"]),
        "video_codec": video["codec_name"],
        "audio_codec": audio["codec_name"],
        "container": container,
        "duration_seconds": duration,
        "render_exit_code": 0,
        "content_sha256": content_sha256(VIDEO_PATH),
        "uploaded_hashes": episode.get("uploaded_hashes", []),
        "rights": {"assets": [{
            "origin": "Generated by WhySpark Pillow vector renderer and espeak-ng",
            "rights_status": "original_project_generated",
            "creator": "WhySpark automation",
            "license": "project-original",
            "third_party_media": False,
        }]},
    }
    (ARTIFACTS / "render-report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "rendered", "report": str(ARTIFACTS / "render-report.json"), "bytes": size,
                      "duration_seconds": duration, "sha256": result["content_sha256"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RENDER BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
