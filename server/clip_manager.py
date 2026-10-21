import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from server.config import OUTPUT_DIR, TEMP_DIR
from server.yt_engine import download_clip_segment, format_seconds
from server.video_processor import render_clip, probe_video

logger = logging.getLogger("clip_manager")

HISTORY_FILE = OUTPUT_DIR / "history.json"

class ClipTaskManager:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if HISTORY_FILE.is_file():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error("Failed to save history: %s", e)

    def create_task(self, params: Dict[str, Any]) -> str:
        task_id = uuid.uuid4().hex[:12]
        self.tasks[task_id] = {
            "id": task_id,
            "status": "pending",
            "progress": 5,
            "message": "Initializing task pipeline...",
            "params": params,
            "result": None,
            "error": None,
            "created_at": time.time()
        }
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.tasks.get(task_id)

    def get_all_clips(self) -> List[Dict[str, Any]]:
        # Check files still exist on disk
        valid_history = []
        for item in self.history:
            filepath = OUTPUT_DIR / item.get("filename", "")
            if filepath.is_file():
                valid_history.append(item)
        if len(valid_history) != len(self.history):
            self.history = valid_history
            self._save_history()
        return self.history

    def delete_clip(self, filename: str) -> bool:
        filepath = OUTPUT_DIR / filename
        if filepath.is_file():
            try:
                filepath.unlink()
            except Exception:
                pass
        self.history = [h for h in self.history if h.get("filename") != filename]
        self._save_history()
        return True

    async def execute_task(self, task_id: str):
        task = self.tasks.get(task_id)
        if not task:
            return

        params = task["params"]
        url = params["url"]
        start_sec = float(params.get("start_sec", 0))
        end_sec = float(params.get("end_sec", start_sec + 30))
        style = params.get("style", "blur_9_16")
        headline_text = params.get("headline_text")
        headline_style = params.get("headline_style", "yellow")
        progress_bar = params.get("progress_bar", True)
        watermark = params.get("watermark")
        audio_boost = float(params.get("audio_boost", 1.0))
        title = params.get("title", "YouTube Clip")
        thumbnail = params.get("thumbnail", "")

        raw_segment_path = str(TEMP_DIR / f"raw_{task_id}.mp4")
        final_filename = f"clip_{task_id}.mp4"
        final_output_path = str(OUTPUT_DIR / final_filename)

        async def _update_status(status_name: str, message: str, progress: int):
            task["status"] = status_name
            task["message"] = message
            task["progress"] = progress

        try:
            # 1. Download slice via yt-dlp
            await _update_status("downloading", "Downloading video slice directly from YouTube...", 20)
            await download_clip_segment(
                url=url,
                start_sec=start_sec,
                end_sec=end_sec,
                output_path=raw_segment_path,
                status_callback=_update_status
            )

            # 2. Render & format via FFmpeg
            await _update_status("rendering", "Rendering 9:16 vertical short with FFmpeg filters...", 60)
            await render_clip(
                input_video=raw_segment_path,
                output_video=final_output_path,
                style=style,
                headline_text=headline_text,
                headline_style=headline_style,
                progress_bar=progress_bar,
                watermark=watermark,
                audio_boost=audio_boost,
                status_callback=_update_status
            )

            # Probe final video info
            probe = probe_video(final_output_path)
            file_size_mb = round(os.path.getsize(final_output_path) / (1024 * 1024), 2)

            result_data = {
                "id": task_id,
                "filename": final_filename,
                "download_url": f"/api/download/{final_filename}",
                "stream_url": f"/output/{final_filename}",
                "title": title,
                "thumbnail": thumbnail,
                "duration": probe["duration"],
                "duration_formatted": format_seconds(probe["duration"]),
                "width": probe["width"],
                "height": probe["height"],
                "file_size_mb": file_size_mb,
                "style": style,
                "headline": headline_text,
                "created_at": time.time(),
                "created_at_formatted": time.strftime("%b %d, %H:%M")
            }

            task["status"] = "completed"
            task["progress"] = 100
            task["message"] = "Clip generated successfully!"
            task["result"] = result_data

            # Save to persistent history (most recent first)
            self.history.insert(0, result_data)
            self._save_history()

        except Exception as e:
            logger.exception("Task %s failed: %s", task_id, e)
            task["status"] = "failed"
            task["progress"] = 100
            task["error"] = str(e)
            task["message"] = f"Failed: {str(e)[:200]}"

        finally:
            # Clean up intermediate raw download
            if os.path.isfile(raw_segment_path):
                try:
                    os.remove(raw_segment_path)
                except Exception:
                    pass

clip_manager = ClipTaskManager()
