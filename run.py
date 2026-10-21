import sys
import os

# Ensure safe utf-8 stdout on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn
from server.config import FFMPEG_PATH, NODE_PATH, YT_DLP_PATH, HOST, PORT

def main():
    print("=" * 60)
    print("  [+] ClipFlow AI - YouTube Shorts & Video Clipper Studio")
    print("=" * 60)
    print(f"  -> Web Interface:   http://{HOST}:{PORT}")
    print(f"  -> API Docs:        http://{HOST}:{PORT}/docs")
    print(f"  -> FFmpeg:          {FFMPEG_PATH or 'NOT DETECTED'}")
    print(f"  -> Node.js:         {NODE_PATH or 'NOT DETECTED'}")
    print(f"  -> yt-dlp:          {YT_DLP_PATH or 'NOT DETECTED'}")
    print("=" * 60)
    print("  Starting server... Press Ctrl+C to stop.\n")

    uvicorn.run("server.app:app", host=HOST, port=PORT, reload=False)

if __name__ == "__main__":
    main()
