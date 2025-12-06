"""
VideoNote Python Sidecar - FastAPI Backend
This service handles video processing tasks including downloading and analysis.
"""

import sys
import socket
from contextlib import asynccontextmanager
from typing import Dict, Optional

import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.downloader import download_video, DownloadProgress


# Response models
class StatusResponse(BaseModel):
    status: str
    message: str


class DownloadRequest(BaseModel):
    url: str
    save_path: str
    format_preference: Optional[str] = "best"


class DownloadResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None
    file_path: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = None
    thumbnail: Optional[str] = None


# Application lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    print("Python Sidecar starting up...", file=sys.stderr)
    yield
    # Shutdown
    print("Python Sidecar shutting down...", file=sys.stderr)


# Create FastAPI application
app = FastAPI(
    title="VideoNote Python Sidecar",
    description="Backend service for video processing",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS to allow Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes
@app.get("/", response_model=StatusResponse)
async def root():
    """Health check endpoint."""
    return StatusResponse(
        status="ok",
        message="Python Sidecar is running"
    )


@app.get("/health", response_model=StatusResponse)
async def health():
    """Alternative health check endpoint."""
    return StatusResponse(
        status="ok",
        message="Python Sidecar is healthy"
    )


# Global dictionary to track download status
download_tasks: Dict[str, Dict] = {}


def progress_callback_factory(task_id: str):
    """
    Create a progress callback for a specific download task.

    Args:
        task_id: Unique identifier for the download task

    Returns:
        Callback function that updates the task status
    """
    def callback(progress: DownloadProgress):
        if task_id in download_tasks:
            download_tasks[task_id]["progress"] = {
                "status": progress.status,
                "percent": progress.percent,
                "speed": progress.speed,
                "eta": progress.eta,
                "filename": progress.filename,
            }
    return callback


def download_task(task_id: str, url: str, save_path: str, format_preference: str):
    """
    Background task to download a video.

    Args:
        task_id: Unique identifier for this download
        url: Video URL to download
        save_path: Path to save the video
        format_preference: Video format preference
    """
    try:
        print(f"Starting download task {task_id}: {url}", file=sys.stderr)

        # Update task status
        download_tasks[task_id]["status"] = "downloading"

        # Create progress callback
        callback = progress_callback_factory(task_id)

        # Download the video
        result = download_video(
            url=url,
            save_path=save_path,
            progress_callback=callback,
            ffmpeg_location=None,  # Will auto-detect
        )

        # Update task with result
        download_tasks[task_id].update({
            "status": "completed" if result["success"] else "failed",
            "result": result,
        })

        print(f"Download task {task_id} completed: {result['success']}", file=sys.stderr)

    except Exception as e:
        error_msg = f"Download task {task_id} failed: {str(e)}"
        print(error_msg, file=sys.stderr)
        download_tasks[task_id].update({
            "status": "failed",
            "result": {
                "success": False,
                "message": error_msg,
            },
        })


@app.post("/api/download", response_model=DownloadResponse)
async def api_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Download a video from the given URL.

    The download runs in the background. Use the task_id to check progress.

    Args:
        request: Download request containing URL and save path
        background_tasks: FastAPI background tasks manager

    Returns:
        DownloadResponse with task_id for tracking
    """
    import uuid

    # Validate URL
    if not request.url or not request.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    # Validate save_path
    if not request.save_path or not request.save_path.strip():
        raise HTTPException(status_code=400, detail="save_path is required")

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Initialize task tracking
    download_tasks[task_id] = {
        "task_id": task_id,
        "url": request.url,
        "save_path": request.save_path,
        "status": "queued",
        "progress": {},
        "result": None,
    }

    # Add download task to background
    background_tasks.add_task(
        download_task,
        task_id,
        request.url,
        request.save_path,
        request.format_preference,
    )

    print(f"Queued download task {task_id} for URL: {request.url}", file=sys.stderr)

    return DownloadResponse(
        success=True,
        message="Download task queued",
        task_id=task_id,
    )


@app.get("/api/download/{task_id}", response_model=DownloadResponse)
async def get_download_status(task_id: str):
    """
    Get the status of a download task.

    Args:
        task_id: Unique identifier for the download task

    Returns:
        DownloadResponse with current status
    """
    if task_id not in download_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = download_tasks[task_id]
    result = task.get("result")

    if result:
        return DownloadResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            task_id=task_id,
            file_path=result.get("file_path"),
            title=result.get("title"),
            duration=result.get("duration"),
            thumbnail=result.get("thumbnail"),
        )
    else:
        return DownloadResponse(
            success=True,
            message=f"Download status: {task['status']}",
            task_id=task_id,
        )


def find_free_port() -> int:
    """Find a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def main():
    """Main entry point for the sidecar."""
    # Use port 0 to get a random available port
    port = find_free_port()

    # Print the port to stdout so Tauri can capture it
    # This is the critical line that Tauri will parse
    print(f"SERVER_PORT={port}", flush=True)

    # Additional logging to stderr (won't interfere with port detection)
    print(f"Starting Python Sidecar on port {port}", file=sys.stderr)

    # Start the uvicorn server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
