import asyncio
import json
import logging
import re
import subprocess
from typing import Dict, Any, Optional

from server.config import FFMPEG_PATH, NODE_PATH, YT_DLP_PATH

logger = logging.getLogger("yt_engine")

def format_seconds(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds is None:
        return "00:00"
    total_sec = int(round(seconds))
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def parse_time_str(time_val: Any) -> float:
    """Parse string '01:23' or '00:01:23.5' or numeric seconds into float seconds."""
    if isinstance(time_val, (int, float)):
        return float(time_val)
    if not isinstance(time_val, str):
        return 0.0
    s = time_val.strip()
    if not s:
        return 0.0
    parts = s.split(":")
    try:
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        else:
            return float(parts[0])
    except ValueError:
        return 0.0

def extract_youtube_id(url: str) -> Optional[str]:
    """Extract 11-char YouTube ID from any YouTube URL or string."""
    patterns = [
        r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def build_ytdlp_cmd(extra_args: list) -> list:
    """Construct base yt-dlp command with node runtime & ffmpeg location."""
    cmd = [YT_DLP_PATH or "yt-dlp"]
    if NODE_PATH:
        cmd.extend(["--js-runtimes", f"node:{NODE_PATH}"])
    if FFMPEG_PATH:
        cmd.extend(["--ffmpeg-location", FFMPEG_PATH])
    cmd.extend(extra_args)
    return cmd

async def get_video_info(url: str) -> Dict[str, Any]:
    """Fetch video metadata using yt-dlp dump-json."""
    yt_id = extract_youtube_id(url)
    clean_url = f"https://www.youtube.com/watch?v={yt_id}" if yt_id else url

    cmd = build_ytdlp_cmd([
        "--dump-json",
        "--no-playlist",
        "--skip-download",
        clean_url
    ])

    loop = asyncio.get_event_loop()
    def _run():
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {res.stderr.strip()[:300]}")
        return json.loads(res.stdout)

    data = await loop.run_in_executor(None, _run)

    duration = data.get("duration") or 0.0
    width = data.get("width") or 1920
    height = data.get("height") or 1080
    is_vertical = height > width or "/shorts/" in url.lower()

    return {
        "id": data.get("id") or yt_id,
        "title": data.get("title", "YouTube Video"),
        "uploader": data.get("uploader", "Unknown Channel"),
        "channel": data.get("channel", data.get("uploader", "Unknown")),
        "duration": duration,
        "duration_formatted": format_seconds(duration),
        "thumbnail": data.get("thumbnail") or (f"https://img.youtube.com/vi/{yt_id}/maxresdefault.jpg" if yt_id else ""),
        "webpage_url": data.get("webpage_url") or clean_url,
        "width": width,
        "height": height,
        "is_vertical": is_vertical,
        "view_count": data.get("view_count", 0),
        "description": (data.get("description") or "")[:250]
    }

async def download_clip_segment(
    url: str,
    start_sec: float,
    end_sec: float,
    output_path: str,
    status_callback=None
) -> str:
    """Download the specific time section using yt-dlp's --download-sections."""
    yt_id = extract_youtube_id(url)
    target_url = f"https://www.youtube.com/watch?v={yt_id}" if yt_id else url

    start_str = format_seconds(start_sec)
    end_str = format_seconds(end_sec)
    section_arg = f"*{start_str}-{end_str}"

    if status_callback:
        await status_callback("downloading", f"Fetching high-quality stream segment ({start_str} - {end_str})...", 30)

    # Best video up to 1080p + best audio, fallback to best
    cmd = build_ytdlp_cmd([
        "--download-sections", section_arg,
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "--merge-output-format", "mp4",
        "--force-overwrites",
        "-o", output_path,
        target_url
    ])

    loop = asyncio.get_event_loop()
    def _run():
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode != 0:
            logger.error("Download failed: %s", res.stderr)
            raise RuntimeError(f"Download failed: {res.stderr.strip()[:300]}")
        return True

    await loop.run_in_executor(None, _run)
    return output_path
