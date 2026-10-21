import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFont

from server.config import FFMPEG_PATH, TEMP_DIR

logger = logging.getLogger("video_processor")

def get_system_font(size: int = 44, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load the best available Windows, Linux, or Replit system TTF font."""
    font_candidates = [
        # Windows Fonts
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        # Linux / Replit Nix Fonts
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/nix/var/nix/profiles/default/share/fonts/truetype/DejaVuSans-Bold.ttf"
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    try:
        # Fallback to font name lookup via fontconfig if available
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()

def create_headline_badge(
    text: str,
    tag_text: str = "VIRAL HOOK",
    style: str = "yellow",
    canvas_w: int = 1080,
    canvas_h: int = 1920,
    output_png: str = None
) -> str:
    """Generate a crisp transparent PNG with a modern YouTube Shorts hook banner."""
    if not output_png:
        output_png = str(TEMP_DIR / f"headline_{os.getpid()}_{id(text)}.png")

    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Style colors
    styles = {
        "yellow": {
            "bg": (14, 14, 20, 235),
            "border": (255, 0, 68, 240),
            "tag_bg": (255, 0, 68, 255),
            "tag_text": (255, 255, 255),
            "text": (255, 232, 0)
        },
        "neon": {
            "bg": (10, 15, 30, 235),
            "border": (0, 240, 255, 230),
            "tag_bg": (138, 43, 226, 255),
            "tag_text": (255, 255, 255),
            "text": (255, 255, 255)
        },
        "red": {
            "bg": (20, 10, 10, 235),
            "border": (255, 50, 50, 240),
            "tag_bg": (255, 30, 30, 255),
            "tag_text": (255, 255, 255),
            "text": (255, 255, 255)
        },
        "glass": {
            "bg": (25, 25, 35, 215),
            "border": (255, 255, 255, 120),
            "tag_bg": (80, 80, 95, 255),
            "tag_text": (255, 255, 255),
            "text": (245, 245, 250)
        }
    }
    theme = styles.get(style, styles["yellow"])

    font = get_system_font(44, bold=True)
    tag_font = get_system_font(22, bold=True)

    # Word wrapping
    words = text.strip().split()
    lines = []
    current_line = ""
    max_text_width = int(canvas_w * 0.78)

    for word in words:
        test = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_text_width and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)

    line_height = 56
    box_w = min(int(canvas_w * 0.88), 940)
    box_h = 46 + len(lines) * line_height + 24
    box_x = (canvas_w - box_w) // 2
    box_y = int(canvas_h * 0.08)  # Position at top 8% of short

    # Subtle drop shadow
    draw.rounded_rectangle(
        [box_x + 6, box_y + 8, box_x + box_w + 6, box_y + box_h + 8],
        radius=26,
        fill=(0, 0, 0, 130)
    )

    # Main banner
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        radius=26,
        fill=theme["bg"],
        outline=theme["border"],
        width=4
    )

    # Pill tag above/embedded
    tag_w = 180
    tag_h = 34
    draw.rounded_rectangle(
        [box_x + 36, box_y - 17, box_x + 36 + tag_w, box_y - 17 + tag_h],
        radius=10,
        fill=theme["tag_bg"]
    )
    draw.text(
        (box_x + 50, box_y - 13),
        tag_text.upper(),
        font=tag_font,
        fill=theme["tag_text"]
    )

    # Text lines
    for i, line in enumerate(lines):
        y_pos = box_y + 40 + i * line_height
        # Measure line to center it or align left with indent
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_x = box_x + (box_w - text_w) // 2
        draw.text((text_x, y_pos), line, font=font, fill=theme["text"])

    img.save(output_png, "PNG")
    return output_png

def probe_video(file_path: str) -> Dict[str, Any]:
    """Inspect video file to get duration, width, height, and fps using ffmpeg."""
    cmd = [
        FFMPEG_PATH or "ffmpeg",
        "-i", file_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    out = res.stderr

    duration = 10.0
    width = 1920
    height = 1080

    import re
    # Duration: 00:01:23.45
    m_dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", out)
    if m_dur:
        hrs, mins, secs = m_dur.groups()
        duration = float(hrs) * 3600 + float(mins) * 60 + float(secs)

    # Stream #0:0: Video: ... 1920x1080
    m_dim = re.search(r"Video:.*?(\d{3,4})x(\d{3,4})", out)
    if m_dim:
        width = int(m_dim.group(1))
        height = int(m_dim.group(2))

    return {
        "duration": duration,
        "width": width,
        "height": height
    }

async def render_clip(
    input_video: str,
    output_video: str,
    style: str = "blur_9_16",
    headline_text: Optional[str] = None,
    headline_style: str = "yellow",
    progress_bar: bool = True,
    watermark: Optional[str] = None,
    audio_boost: float = 1.0,
    status_callback=None
) -> str:
    """Render the clipped segment into the desired aspect ratio and styling with ffmpeg."""
    if status_callback:
        await status_callback("rendering", "Probing video attributes & preparing filters...", 50)

    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, probe_video, input_video)
    dur = info["duration"]
    orig_w = info["width"]
    orig_h = info["height"]
    is_source_vertical = orig_h > orig_w

    inputs = ["-i", input_video]
    filter_chains = []
    overlay_png = None

    # Handle Canvas Layout
    if style == "original" or (is_source_vertical and style == "blur_9_16"):
        # Source is already vertical or user requested original aspect ratio
        canvas_w = orig_w
        canvas_h = orig_h
        current_v = "[0:v]"
    elif style == "crop_9_16":
        # Full bleed 9:16 center crop
        canvas_w = 1080
        canvas_h = 1920
        filter_chains.append(
            f"[0:v]scale=-2:1920:flags=lanczos,crop=1080:1920:(in_w-1080)/2:0[v_crop]"
        )
        current_v = "[v_crop]"
    elif style == "fit_9_16":
        # Clean letterbox on 1080x1920 black canvas
        canvas_w = 1080
        canvas_h = 1920
        filter_chains.append(
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            f"color=s=1080x1920:c=0x08080c:d={dur}[bg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v_fit]"
        )
        current_v = "[v_fit]"
    elif style == "square_1_1":
        # Square 1080x1080 with blurred background
        canvas_w = 1080
        canvas_h = 1080
        filter_chains.append(
            f"[0:v]scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,boxblur=25:5[bg];"
            f"[0:v]scale=1080:-2:flags=lanczos[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v_sq]"
        )
        current_v = "[v_sq]"
    else:
        # Default: blur_9_16 (Gold standard for Shorts)
        canvas_w = 1080
        canvas_h = 1920
        filter_chains.append(
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
            f"[0:v]scale=1080:-2:flags=lanczos[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v_blur]"
        )
        current_v = "[v_blur]"

    # Optional Headline Hook Overlay
    if headline_text and headline_text.strip():
        overlay_png = create_headline_badge(
            text=headline_text.strip(),
            style=headline_style,
            canvas_w=canvas_w,
            canvas_h=canvas_h
        )
        inputs.extend(["-i", overlay_png])
        filter_chains.append(f"{current_v}[1:v]overlay=0:0[v_text]")
        current_v = "[v_text]"

    # Optional Animated Shorts Progress Bar
    if progress_bar and dur > 0.5:
        bar_h = max(8, int(canvas_h * 0.007))
        # Signature YouTube red progress bar animating from left to right across video duration
        filter_chains.append(
            f"{current_v}drawbox=x=0:y=ih-{bar_h}:w='iw*t/{dur:.2f}':h={bar_h}:color=0xFF0033@1:t=fill[v_prog]"
        )
        current_v = "[v_prog]"

    # Optional Watermark Tag
    if watermark and watermark.strip():
        wm = watermark.strip().replace("'", "\\'")
        filter_chains.append(
            f"{current_v}drawtext=text='{wm}':fontcolor=white@0.7:fontsize={int(canvas_h*0.02)}:x=(w-text_w)/2:y=h-{int(canvas_h*0.04)}[v_wm]"
        )
        current_v = "[v_wm]"

    # Audio filters
    audio_args = []
    if audio_boost and audio_boost != 1.0:
        audio_args.extend(["-filter:a", f"volume={audio_boost:.2f}"])

    if status_callback:
        await status_callback("rendering", "Rendering video with FFmpeg hardware accelerated filters...", 75)

    # Build full ffmpeg command
    cmd = [FFMPEG_PATH or "ffmpeg", "-y"]
    cmd.extend(inputs)

    if filter_chains:
        full_filter = ";".join(filter_chains)
        cmd.extend(["-filter_complex", full_filter, "-map", current_v, "-map", "0:a?"])
    else:
        cmd.extend(["-map", "0:v", "-map", "0:a?"])

    cmd.extend(audio_args)
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_video
    ])

    def _execute():
        logger.info("Executing ffmpeg: %s", " ".join(cmd[:12]))
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace"
        )
        if res.returncode != 0:
            logger.error("FFmpeg render failed: %s", res.stderr)
            raise RuntimeError(f"FFmpeg error: {res.stderr[-300:]}")
        return True

    try:
        await loop.run_in_executor(None, _execute)
    finally:
        # Cleanup temporary PNG overlay
        if overlay_png and os.path.isfile(overlay_png):
            try:
                os.remove(overlay_png)
            except Exception:
                pass

    if status_callback:
        await status_callback("completed", "Clip ready to preview and download!", 100)

    return output_video
