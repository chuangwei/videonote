"""
Video Downloader Module
Uses yt-dlp to download videos from various platforms with progress tracking.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

import yt_dlp


@dataclass
class DownloadProgress:
    """Represents download progress information."""
    status: str  # downloading, finished, error
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0  # bytes per second
    eta: int = 0  # estimated time remaining in seconds
    percent: float = 0.0
    filename: str = ""


class VideoDownloader:
    """
    Video downloader using yt-dlp.
    Supports progress tracking and various video platforms.
    """

    def __init__(self, ffmpeg_location: Optional[str] = None):
        """
        Initialize the video downloader.

        Args:
            ffmpeg_location: Path to ffmpeg binary. If None, will search in system PATH.
        """
        self.ffmpeg_location = ffmpeg_location or self._find_ffmpeg()
        self.progress_callback: Optional[Callable[[DownloadProgress], None]] = None

    def _find_ffmpeg(self) -> Optional[str]:
        """
        Find ffmpeg in system PATH or next to the executable.

        Returns:
            Path to ffmpeg or None if not found.
        """
        print(f"[ffmpeg] Platform: {sys.platform}", file=sys.stderr)

        # Method 1: Check next to the executable (NEW - for standalone bundling)
        # This is the workaround for PyInstaller's --add-binary limitation
        exe_dir = Path(sys.executable).parent
        print(f"[ffmpeg] Checking next to executable: {exe_dir}", file=sys.stderr)

        if sys.platform.startswith('win'):
            ffmpeg_exe = exe_dir / "ffmpeg.exe"
            if ffmpeg_exe.exists():
                print(f"[ffmpeg] OK Found ffmpeg.exe next to executable: {ffmpeg_exe}", file=sys.stderr)
                return str(ffmpeg_exe)
            else:
                print(f"[ffmpeg] Not found at: {ffmpeg_exe}", file=sys.stderr)
        else:
            ffmpeg_exe = exe_dir / "ffmpeg"
            if ffmpeg_exe.exists():
                print(f"[ffmpeg] OK Found ffmpeg next to executable: {ffmpeg_exe}", file=sys.stderr)
                return str(ffmpeg_exe)
            else:
                print(f"[ffmpeg] Not found at: {ffmpeg_exe}", file=sys.stderr)

        # Method 2: Check PyInstaller temporary directory (OLD method, kept for compatibility)
        if hasattr(sys, '_MEIPASS'):
            print(f"[ffmpeg] Running from PyInstaller bundle: {sys._MEIPASS}", file=sys.stderr)

            # List contents of _MEIPASS for debugging
            try:
                meipass_files = os.listdir(sys._MEIPASS)
                print(f"[ffmpeg] _MEIPASS contains {len(meipass_files)} files", file=sys.stderr)
                # Show ffmpeg-related files
                ffmpeg_files = [f for f in meipass_files if 'ffmpeg' in f.lower()]
                if ffmpeg_files:
                    print(f"[ffmpeg] Found ffmpeg-related files in _MEIPASS: {ffmpeg_files}", file=sys.stderr)
            except Exception as e:
                print(f"[ffmpeg] Could not list _MEIPASS: {e}", file=sys.stderr)

            # Windows: check for ffmpeg.exe in _MEIPASS
            if sys.platform.startswith('win'):
                ffmpeg_path = os.path.join(sys._MEIPASS, "ffmpeg.exe")
                print(f"[ffmpeg] Checking _MEIPASS: {ffmpeg_path}", file=sys.stderr)
                if os.path.exists(ffmpeg_path):
                    print("[ffmpeg] OK Found bundled ffmpeg.exe in _MEIPASS", file=sys.stderr)
                    return ffmpeg_path
                else:
                    print("[ffmpeg] NOT FOUND in _MEIPASS", file=sys.stderr)
            else:
                # macOS/Linux: check for ffmpeg (no extension) in _MEIPASS
                ffmpeg_path = os.path.join(sys._MEIPASS, "ffmpeg")
                print(f"[ffmpeg] Checking _MEIPASS: {ffmpeg_path}", file=sys.stderr)
                if os.path.exists(ffmpeg_path):
                    print("[ffmpeg] OK Found bundled ffmpeg in _MEIPASS", file=sys.stderr)
                    return ffmpeg_path
                else:
                    print("[ffmpeg] NOT FOUND in _MEIPASS", file=sys.stderr)

        # Method 3: Check system PATH as final fallback
        print("[ffmpeg] Checking system PATH...", file=sys.stderr)
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            print(f"[ffmpeg] OK Found ffmpeg in system PATH: {ffmpeg_path}", file=sys.stderr)
            return ffmpeg_path
        else:
            print("[ffmpeg] NOT FOUND: ffmpeg not found in system PATH", file=sys.stderr)
            return None

    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """
        Hook called by yt-dlp to report download progress.

        Args:
            d: Progress dictionary from yt-dlp
        """
        if not self.progress_callback:
            return

        status = d.get("status", "unknown")

        if status == "downloading":
            progress = DownloadProgress(
                status="downloading",
                downloaded_bytes=d.get("downloaded_bytes", 0),
                total_bytes=d.get("total_bytes", 0) or d.get("total_bytes_estimate", 0),
                speed=d.get("speed", 0.0) or 0.0,
                eta=d.get("eta", 0) or 0,
                filename=d.get("filename", ""),
            )

            # Calculate percentage
            if progress.total_bytes > 0:
                progress.percent = (progress.downloaded_bytes / progress.total_bytes) * 100
            else:
                progress.percent = 0.0

            # Print progress to stderr for debugging
            print(
                f"Downloading: {progress.percent:.1f}% | "
                f"Speed: {progress.speed / 1024 / 1024:.2f} MB/s | "
                f"ETA: {progress.eta}s",
                file=sys.stderr,
            )

            self.progress_callback(progress)

        elif status == "finished":
            progress = DownloadProgress(
                status="finished",
                filename=d.get("filename", ""),
                percent=100.0,
            )
            print(f"Download finished: {progress.filename}", file=sys.stderr)
            self.progress_callback(progress)

        elif status == "error":
            progress = DownloadProgress(
                status="error",
                filename=d.get("filename", ""),
            )
            print(f"Download error: {progress.filename}", file=sys.stderr)
            self.progress_callback(progress)

    def download_video(
        self,
        url: str,
        save_path: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        format_preference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Download a video from the given URL.

        Args:
            url: Video URL to download
            save_path: Directory or file path to save the video
            progress_callback: Optional callback function for progress updates
            format_preference: Video format preference (default: None, which uses QuickTime compatible settings)
                Options: "best", "worst", "bestvideo+bestaudio", etc.

        Returns:
            Dict containing:
                - success: bool
                - message: str
                - file_path: str (if successful)
                - title: str (video title)
                - duration: int (video duration in seconds)
                - thumbnail: str (thumbnail URL)

        Raises:
            Exception: If download fails
        """
        self.progress_callback = progress_callback

        # Ensure save_path is a directory
        save_dir = Path(save_path)
        if save_dir.suffix:  # If it has an extension, treat as file
            save_dir = save_dir.parent
        save_dir.mkdir(parents=True, exist_ok=True)

        # Set default format preference if not provided
        # We prioritize mp4/h264 for better compatibility (e.g. QuickTime)
        if not format_preference or format_preference == "best":
            if self.ffmpeg_location:
                # If ffmpeg is available, we can merge separate video/audio streams
                format_preference = "bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                print("[ffmpeg] Using format with potential merge (ffmpeg available)", file=sys.stderr)
            else:
                # If ffmpeg is NOT available, only download pre-merged formats
                format_preference = "best[ext=mp4]/best"
                print("[ffmpeg] Using pre-merged format only (ffmpeg unavailable)", file=sys.stderr)

        # Configure yt-dlp options
        ydl_opts = {
            "format": format_preference,
            "outtmpl": str(save_dir / "%(title)s.%(ext)s"),
            "progress_hooks": [self._progress_hook],
            "quiet": False,
            "no_warnings": False,
            "extract_flat": False,
        }

        # Add ffmpeg location if available
        if self.ffmpeg_location:
            print(f"[ffmpeg] Configuring yt-dlp with ffmpeg: {self.ffmpeg_location}", file=sys.stderr)
            ydl_opts["ffmpeg_location"] = self.ffmpeg_location
            # Force output to mp4 container for better compatibility
            ydl_opts["merge_output_format"] = "mp4"
            # Ensure final output is mp4 even if source wasn't
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }]
        else:
            print("[ffmpeg] WARNING: ffmpeg not available, downloading pre-merged formats only", file=sys.stderr)
            print("[ffmpeg] Some videos may not be available in highest quality", file=sys.stderr)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first (without downloading)
                print(f"Extracting video info from: {url}", file=sys.stderr)
                info = ydl.extract_info(url, download=False)

                if info is None:
                    raise Exception("Failed to extract video information")

                # Get video metadata
                video_title = info.get("title", "Unknown")
                video_duration = info.get("duration", 0)
                video_thumbnail = info.get("thumbnail", "")

                print(f"Downloading: {video_title}", file=sys.stderr)
                print(f"Duration: {video_duration}s", file=sys.stderr)

                # Download the video
                ydl.download([url])

                # Find the downloaded file
                downloaded_file = save_dir / f"{video_title}.{info.get('ext', 'mp4')}"

                # Sometimes yt-dlp modifies the filename, so we need to find it
                if not downloaded_file.exists():
                    # Search for recently created files
                    files = list(save_dir.glob("*"))
                    if files:
                        downloaded_file = max(files, key=lambda f: f.stat().st_mtime)

                return {
                    "success": True,
                    "message": "Download completed successfully",
                    "file_path": str(downloaded_file),
                    "title": video_title,
                    "duration": video_duration,
                    "thumbnail": video_thumbnail,
                }

        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(error_msg, file=sys.stderr)
            return {
                "success": False,
                "message": error_msg,
                "file_path": "",
                "title": "",
                "duration": 0,
                "thumbnail": "",
            }


def download_video(
    url: str,
    save_path: str,
    progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ffmpeg_location: Optional[str] = None,
    format_preference: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to download a video.

    Args:
        url: Video URL to download
        save_path: Directory or file path to save the video
        progress_callback: Optional callback function for progress updates
        ffmpeg_location: Optional path to ffmpeg binary
        format_preference: Video format preference

    Returns:
        Dict containing download results
    """
    downloader = VideoDownloader(ffmpeg_location=ffmpeg_location)
    return downloader.download_video(url, save_path, progress_callback, format_preference)
