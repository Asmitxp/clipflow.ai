import os
import sys
import shutil
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Locate FFmpeg binary
FFMPEG_PATH = None
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass

if not FFMPEG_PATH or not os.path.isfile(FFMPEG_PATH):
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        FFMPEG_PATH = system_ffmpeg

# Locate Node binary (critical for yt-dlp JavaScript extraction runtime on YouTube)
NODE_PATH = shutil.which("node")
if not NODE_PATH:
    if os.path.isfile(r"C:\nodejs\node.exe"):
        NODE_PATH = r"C:\nodejs\node.exe"

# Locate yt-dlp binary
YT_DLP_PATH = shutil.which("yt-dlp")
if not YT_DLP_PATH:
    py_scripts = Path(sys.executable).parent / "Scripts" / "yt-dlp.exe"
    if py_scripts.is_file():
        YT_DLP_PATH = str(py_scripts)
    elif shutil.which("yt-dlp"):
        YT_DLP_PATH = shutil.which("yt-dlp")
    else:
        YT_DLP_PATH = "yt-dlp"

# Server Config (Replit requires 0.0.0.0 to bind externally)
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8080))
MAX_CLIP_DURATION = 300  # 5 minutes maximum per clip
