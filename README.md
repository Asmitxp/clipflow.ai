# ⚡ ClipFlow AI — YouTube to 9:16 Shorts Studio

A fullstack web application that transforms any YouTube video link into studio-grade **9:16 Shorts, TikToks, and Instagram Reels** with visual timeline scrubbing, smart blurred background framing, customizable viral hook banners, animated progress bars, and fast-start MP4 exporting.

---

## 🌟 Key Features

1. **Paste & Auto-Inspect**:
   - Supports all YouTube URLs (Standard `watch?v=...`, Shortened `youtu.be/...`, or Shorts `youtube.com/shorts/...`).
   - Fetches title, channel name, duration, and thumbnail.
   - Embeds an interactive player for previewing the video.

2. **Visual Dual-Handle Timeline Trimmer**:
   - Interactive dual range slider with Start and End thumbs.
   - Quick presets for Shorts formats: **15s**, **30s**, and **60s**.
   - Precise manual millisecond steppers (+1s / -1s).

3. **Shorts / Reels Framing & Styling Modes**:
   - **Smart Blur (9:16)** *(Recommended)*: Centers your video sharply while filling the top and bottom with a dynamic, zoomed ambient blur (the gold standard for converting horizontal videos to viral shorts).
   - **Center Crop (9:16)**: Full-bleed vertical center zoom.
   - **Letterbox (9:16)**: Fits full video with sleek black margins.
   - **Original Ratio**: Preserves native dimensions (perfect if the source is already 9:16 vertical).

4. **Viral Shorts Enhancements**:
   - **Hook Headline Banner**: Add top text overlays (e.g., *"NO WAY MRBEAST DID THIS! 😱"*) with styles like *Viral Yellow Badge*, *Cyber Neon*, *Fire Red*, or *Glass Pill*.
   - **Animated Red Progress Bar**: Classic YouTube Shorts red timeline line advancing along the bottom.
   - **Audio Booster**: Dialogue volume amplifier (100%, 125%, 150%).
   - **Creator Handle / Watermark**: Optional bottom watermark tag.

5. **Fast Stream Slicing & Export**:
   - Uses `yt-dlp` slice streaming (`--download-sections`) to download only the required seconds rather than the full multi-gigabyte video.
   - Uses hardware-accelerated `FFmpeg` filterchains with `libx264` and `+faststart` MP4 encoding.
   - In-mockup iPhone smartphone preview player with instant MP4 download button.
   - Persistent Recent Clips Gallery with re-download and deletion capabilities.

---

## 🛠️ Architecture & Tech Stack

- **Backend**: Python 3.14 + [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **Media Engine**: [yt-dlp](https://github.com/yt-dlp/yt-dlp) + [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) (FFmpeg v7.1) + [Pillow](https://python-pillow.org/)
- **Frontend**: Responsive Single-Page Application with Vanilla HTML5, Vanilla CSS (Glassmorphism & Obsidian Dark Mode), and Vanilla ES6+ JavaScript.

---

## 🚀 Running Locally

1. Open your terminal in this directory:
   ```powershell
   cd c:\Users\asmit\OneDrive\Desktop\cliping
   ```

2. Run the application:
   ```powershell
   python run.py
   ```

3. Open your browser and navigate to:
   - **Web Studio**: [http://127.0.0.1:8080](http://127.0.0.1:8080)
   - **Interactive API Docs**: [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)
