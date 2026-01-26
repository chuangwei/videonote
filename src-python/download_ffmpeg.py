"""
Auto-download ffmpeg binary files for packaging
macOS only - uses Homebrew-installed ffmpeg
"""

import os
import sys
import platform
import shutil
from pathlib import Path


def get_platform_key():
    """Get platform identifier"""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    else:
        raise Exception(f"Unsupported platform: {system}. This application only supports macOS.")


def get_ffmpeg_from_homebrew(cache_dir):
    """
    Get ffmpeg from Homebrew installation

    Args:
        cache_dir: Cache directory for ffmpeg binary

    Returns:
        Path to ffmpeg executable
    """
    executable_name = "ffmpeg"

    # Check if already cached
    cached_ffmpeg = cache_dir / executable_name
    if cached_ffmpeg.exists():
        print(f"Using cached ffmpeg: {cached_ffmpeg}")
        return str(cached_ffmpeg)

    # Try to use system-installed ffmpeg
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        print(f"Using system ffmpeg: {system_ffmpeg}")
        # Copy to cache directory
        shutil.copy2(system_ffmpeg, cached_ffmpeg)
        # Set executable permissions
        os.chmod(cached_ffmpeg, 0o755)
        return str(cached_ffmpeg)
    else:
        raise Exception("ffmpeg not found on macOS. Please install with 'brew install ffmpeg'")


def get_ffmpeg_path(target_platform=None):
    """
    Get ffmpeg path from Homebrew installation

    Args:
        target_platform: Ignored (kept for compatibility). Only macOS is supported.

    Returns:
        Path to ffmpeg executable
    """
    # Verify we're on macOS
    platform_key = get_platform_key()

    # Create cache directory
    script_dir = Path(__file__).parent
    cache_dir = script_dir / ".ffmpeg_cache" / "darwin"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"Getting ffmpeg for macOS")
    print(f"{'='*50}")

    try:
        ffmpeg_path = get_ffmpeg_from_homebrew(cache_dir)
        print(f"\nffmpeg ready: {ffmpeg_path}")
        return ffmpeg_path
    except Exception as e:
        print(f"\nFailed to get ffmpeg: {e}")
        raise


if __name__ == "__main__":
    try:
        ffmpeg_path = get_ffmpeg_path()
        print(f"\nSuccess! ffmpeg path: {ffmpeg_path}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
