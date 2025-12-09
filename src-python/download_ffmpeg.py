"""
Auto-download ffmpeg binary files for packaging
Supports Windows, macOS, Linux
"""

import os
import sys
import platform
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path


FFMPEG_VERSIONS = {
    "windows": {
        "url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
        "executable": "ffmpeg.exe",
    },
    "darwin": {
        # For macOS, we use system-installed ffmpeg
        "url": None,
        "executable": "ffmpeg",
    },
    "linux": {
        "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
        "executable": "ffmpeg",
    }
}


def get_platform_key():
    """Get platform identifier"""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        raise Exception(f"Unsupported platform: {system}")


def download_file(url, dest_path):
    """Download file and show progress"""
    print(f"Downloading: {url}")
    
    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(downloaded * 100.0 / total_size, 100)
            sys.stdout.write(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)")
            sys.stdout.flush()
    
    urllib.request.urlretrieve(url, dest_path, reporthook)
    print("\nDownload complete!")


def extract_zip(zip_path, extract_to):
    """Extract ZIP file"""
    print(f"Extracting: {zip_path}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print("Extraction complete!")


def extract_tar(tar_path, extract_to):
    """Extract TAR file"""
    print(f"Extracting: {tar_path}")
    with tarfile.open(tar_path, 'r:*') as tar_ref:
        tar_ref.extractall(extract_to)
    print("Extraction complete!")


def find_ffmpeg_in_directory(directory, executable_name):
    """Recursively find ffmpeg executable in directory"""
    for root, dirs, files in os.walk(directory):
        if executable_name in files:
            return os.path.join(root, executable_name)
    return None


def download_ffmpeg_for_platform(platform_key, cache_dir):
    """
    Download ffmpeg for specified platform
    
    Args:
        platform_key: Platform identifier (windows/darwin/linux)
        cache_dir: Cache directory
    
    Returns:
        Path to ffmpeg executable
    """
    config = FFMPEG_VERSIONS.get(platform_key)
    if not config:
        raise Exception(f"Unsupported platform: {platform_key}")
    
    executable_name = config["executable"]
    
    # Check if already downloaded
    cached_ffmpeg = cache_dir / executable_name
    if cached_ffmpeg.exists():
        print(f"Using cached ffmpeg: {cached_ffmpeg}")
        return str(cached_ffmpeg)
    
    # For macOS, try to use system-installed ffmpeg
    if platform_key == "darwin":
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            print(f"Using system ffmpeg: {system_ffmpeg}")
            # Copy to cache directory
            shutil.copy2(system_ffmpeg, cached_ffmpeg)
            return str(cached_ffmpeg)
        else:
            raise Exception("ffmpeg not found on macOS, please install with 'brew install ffmpeg'")
    
    url = config.get("url")
    if not url:
        raise Exception(f"Platform {platform_key} has no download URL configured")
    
    # Create temporary download directory
    download_dir = cache_dir / "temp_download"
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine file extension
    if url.endswith('.zip'):
        archive_path = download_dir / "ffmpeg.zip"
        extract_func = extract_zip
    elif url.endswith('.tar.xz') or url.endswith('.tar.gz'):
        archive_path = download_dir / "ffmpeg.tar.xz"
        extract_func = extract_tar
    else:
        raise Exception(f"Unsupported archive format: {url}")
    
    try:
        # Download archive file
        download_file(url, archive_path)
        
        # Extract
        extract_to = download_dir / "extracted"
        extract_to.mkdir(exist_ok=True)
        extract_func(archive_path, extract_to)
        
        # Find ffmpeg executable
        ffmpeg_path = find_ffmpeg_in_directory(extract_to, executable_name)
        if not ffmpeg_path:
            raise Exception(f"{executable_name} not found in extracted files")
        
        print(f"Found ffmpeg: {ffmpeg_path}")
        
        # Copy to cache directory
        shutil.copy2(ffmpeg_path, cached_ffmpeg)

        # Set executable permissions on Unix systems
        if platform_key != "windows":
            os.chmod(cached_ffmpeg, 0o755)

        # Verify the copied file
        if not cached_ffmpeg.exists():
            raise Exception(f"Failed to copy ffmpeg to {cached_ffmpeg}")

        file_size = cached_ffmpeg.stat().st_size
        print(f"ffmpeg saved to: {cached_ffmpeg} (size: {file_size} bytes)")
        return str(cached_ffmpeg)
        
    finally:
        # Clean up temporary files
        if download_dir.exists():
            shutil.rmtree(download_dir)


def get_ffmpeg_path(target_platform=None):
    """
    Get ffmpeg path, auto-download if not exists
    
    Args:
        target_platform: Target platform (windows/darwin/linux), uses current platform if None
    
    Returns:
        Path to ffmpeg executable
    """
    if target_platform is None:
        target_platform = get_platform_key()
    
    # Create cache directory
    script_dir = Path(__file__).parent
    cache_dir = script_dir / ".ffmpeg_cache" / target_platform
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*50}")
    print(f"Getting ffmpeg for platform: {target_platform}")
    print(f"{'='*50}")
    
    try:
        ffmpeg_path = download_ffmpeg_for_platform(target_platform, cache_dir)
        print(f"\nffmpeg ready: {ffmpeg_path}")
        return ffmpeg_path
    except Exception as e:
        print(f"\nFailed to get ffmpeg: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download ffmpeg binary")
    parser.add_argument(
        "--platform",
        choices=["windows", "darwin", "linux"],
        help="Target platform (defaults to current platform)"
    )
    args = parser.parse_args()
    
    try:
        ffmpeg_path = get_ffmpeg_path(args.platform)
        print(f"\nSuccess! ffmpeg path: {ffmpeg_path}")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
