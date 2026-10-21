import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional

from server.config import STATIC_DIR, OUTPUT_DIR, FFMPEG_PATH, NODE_PATH, YT_DLP_PATH
from server.yt_engine import get_video_info, parse_time_str
from server.clip_manager import clip_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI(title="ClipFlow - YouTube Shorts Studio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class InfoRequest(BaseModel):
    url: str

class ClipRequest(BaseModel):
    url: str
    start_sec: float = 0.0
    end_sec: float = 30.0
    style: str = "blur_9_16"
    headline_text: Optional[str] = None
    headline_style: str = "yellow"
    progress_bar: bool = True
    watermark: Optional[str] = None
    audio_boost: float = 1.0
    title: Optional[str] = "YouTube Clip"
    thumbnail: Optional[str] = ""

# API Endpoints
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "ffmpeg": bool(FFMPEG_PATH),
        "ffmpeg_path": FFMPEG_PATH,
        "node": bool(NODE_PATH),
        "node_path": NODE_PATH,
        "yt_dlp": bool(YT_DLP_PATH),
        "yt_dlp_path": YT_DLP_PATH
    }

@app.post("/api/info")
async def fetch_info(req: InfoRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="Please enter a valid YouTube URL.")
    try:
        info = await get_video_info(req.url.strip())
        return info
    except Exception as e:
        logger.error("Error fetching video info: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to fetch video: {str(e)}")

@app.post("/api/clip")
async def start_clipping(req: ClipRequest, background_tasks: BackgroundTasks):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="Missing YouTube URL.")
    
    start = max(0.0, float(req.start_sec))
    end = float(req.end_sec)
    if end <= start:
        raise HTTPException(status_code=400, detail="End time must be greater than start time.")
    
    duration = end - start
    if duration > 300:
        raise HTTPException(status_code=400, detail="Maximum clip duration is 5 minutes (300 seconds).")

    params = req.model_dump()
    params["start_sec"] = start
    params["end_sec"] = end

    task_id = clip_manager.create_task(params)
    background_tasks.add_task(clip_manager.execute_task, task_id)

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Clip processing scheduled."
    }

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    task = clip_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task

@app.get("/api/clips")
async def get_clips():
    clips = clip_manager.get_all_clips()
    return {"clips": clips}

@app.delete("/api/clips/{filename}")
async def delete_clip_endpoint(filename: str):
    success = clip_manager.delete_clip(filename)
    return {"success": success}

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found or expired.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4"
    )

# Serve generated videos directly for HTML5 preview
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# Serve frontend static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(str(index_file))
    return JSONResponse({"status": "Frontend loading..."})
