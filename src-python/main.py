"""
VideoNote Python Sidecar - FastAPI Backend
This service handles video processing tasks including downloading and analysis.
"""

import sys
import socket
import io
import os
from contextlib import asynccontextmanager
from typing import Dict, Optional

# Fix for Windows output buffering/encoding issues
if sys.platform.startswith('win'):
    # Force utf-8 encoding for stdout/stderr to avoid cp1252 encoding issues
    if sys.stdout:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    if sys.stderr:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

    # Disable Windows-specific output buffering
    os.environ['PYTHONUNBUFFERED'] = '1'


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
    format_preference: Optional[str] = None


class DownloadResponse(BaseModel):
    success: bool
    message: str
    task_id: Optional[str] = None
    file_path: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = None
    thumbnail: Optional[str] = None
    progress: Optional[Dict] = None


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
    allow_origins=["http://localhost:1420", "tauri://localhost", "http://localhost", "https://tauri.localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"^(http://localhost:\d+|tauri://.*)$",
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


def download_task(task_id: str, url: str, save_path: str, format_preference: Optional[str]):
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
            format_preference=format_preference,
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
            progress=task.get("progress")
        )


def find_free_port() -> int:
    """Find a free port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def main():
    """Main entry point for the sidecar."""
    import argparse
    import threading
    import time

    parser = argparse.ArgumentParser(description="VideoNote Python Sidecar")
    parser.add_argument("--port", type=int, help="Port to run the server on (0 for auto-assign)", default=0)
    args = parser.parse_args()

    try:
        # Use port 0 to let the system auto-assign a free port
        if args.port == 0:
            port = find_free_port()
        else:
            port = args.port

        # Print diagnostic info to stderr
        print(f"[INIT] Python version: {sys.version}", file=sys.stderr, flush=True)
        print(f"[INIT] Platform: {sys.platform}", file=sys.stderr, flush=True)
        print(f"[INIT] Working directory: {os.getcwd()}", file=sys.stderr, flush=True)
        print(f"[INIT] Selected port: {port}", file=sys.stderr, flush=True)

        # Flag to track when server is ready
        server_ready = threading.Event()

        def wait_and_announce():
            """Wait for server to be ready, then announce the port."""
            # Wait a bit longer on Windows for uvicorn to fully initialize
            wait_time = 3.0 if sys.platform.startswith('win') else 1.5
            print(f"[INFO] Waiting {wait_time}s for server initialization...", file=sys.stderr, flush=True)
            time.sleep(wait_time)

            # Try to connect to verify server is ready
            max_attempts = 20  # More attempts for Windows
            for attempt in range(max_attempts):
                try:
                    # Explicitly use IPv4 socket
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(2)
                        result = s.connect_ex(('127.0.0.1', port))
                        if result == 0:
                            # Server is accepting connections
                            print(f"[INFO] Server is ready on port {port}", file=sys.stderr, flush=True)

                            # Print the port to stdout so Tauri can capture it
                            # CRITICAL: This must be on its own line and immediately flushed
                            print(f"SERVER_PORT={port}", flush=True)

                            # Triple flush for Windows reliability
                            sys.stdout.flush()
                            if sys.platform.startswith('win'):
                                sys.stdout.flush()
                                sys.stdout.flush()

                            server_ready.set()
                            print(f"[INFO] Port announcement complete", file=sys.stderr, flush=True)
                            return
                except Exception as e:
                    if attempt % 5 == 0:  # Only log every 5th attempt to reduce noise
                        print(f"[DEBUG] Connection attempt {attempt + 1}/{max_attempts}: {e}", file=sys.stderr, flush=True)

                time.sleep(0.5)

            # If we get here, server didn't start properly but announce anyway
            print(f"[WARN] Could not verify server readiness after {max_attempts} attempts ({max_attempts * 0.5:.1f}s)", file=sys.stderr, flush=True)
            print(f"[WARN] Announcing port anyway - frontend will continue retrying", file=sys.stderr, flush=True)
            print(f"SERVER_PORT={port}", flush=True)
            sys.stdout.flush()

        # Start the announcement thread
        announce_thread = threading.Thread(target=wait_and_announce, daemon=True)
        announce_thread.start()

        # Additional logging to stderr (won't interfere with port detection)
        print(f"[START] Starting Python Sidecar on 127.0.0.1:{port}", file=sys.stderr, flush=True)

        # Start the uvicorn server
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info",
        )
    except Exception as e:
        print(f"[ERROR] Failed to start sidecar: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
