import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

# Import auto-download ffmpeg module
try:
    from download_ffmpeg import get_ffmpeg_path as auto_get_ffmpeg
except ImportError:
    auto_get_ffmpeg = None

def get_ffmpeg_path(target_platform=None):
    """
    Get ffmpeg path, with auto-download support
    
    Args:
        target_platform: Target platform (windows/darwin/linux)
    
    Returns:
        Path to ffmpeg executable
    """
    # First try to auto-download/get ffmpeg
    if auto_get_ffmpeg:
        try:
            print("Attempting to auto-get ffmpeg...")
            return auto_get_ffmpeg(target_platform)
        except Exception as e:
            print(f"Auto-get ffmpeg failed: {e}")
            print("Falling back to system PATH search...")
    
    # Fall back to checking system PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        print("\n" + "="*60)
        print("Error: ffmpeg not found")
        print("="*60)
        print("\nPlease install ffmpeg using one of the following methods:")
        print("\nMethod 1: Use package manager")
        print("  macOS:   brew install ffmpeg")
        print("  Windows: choco install ffmpeg")
        print("  Linux:   sudo apt-get install ffmpeg")
        print("\nMethod 2: Use auto-download script")
        print("  python download_ffmpeg.py --platform windows")
        print("\n" + "="*60)
        sys.exit(1)
    
    return ffmpeg_path

def get_target_triple():
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "darwin":
        if machine == "arm64":
            return "aarch64-apple-darwin"
        else:
            return "x86_64-apple-darwin"
    elif system == "linux":
        return "x86_64-unknown-linux-gnu"
    elif system == "windows":
        return "x86_64-pc-windows-msvc"
    else:
        print(f"Unsupported platform: {system} {machine}")
        sys.exit(1)

def build_sidecar(target_platform=None):
    """
    Build Python Sidecar
    
    Args:
        target_platform: Target platform (windows/darwin/linux), defaults to current platform if None
    """
    print("================================================")
    print("Building VideoNote Python Sidecar (Python Script)")
    print("================================================")

    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    output_dir = project_root / "src-tauri" / "binaries"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine target platform
    if target_platform:
        print(f"Target platform (specified): {target_platform}")
        # Convert platform name to target triple
        platform_map = {
            "windows": "x86_64-pc-windows-msvc",
            "darwin": get_target_triple(),  # Use current system architecture
            "linux": "x86_64-unknown-linux-gnu",
        }
        target_triple = platform_map.get(target_platform, get_target_triple())
    else:
        target_triple = get_target_triple()
        target_platform = platform.system().lower()
    
    binary_name = f"vn-sidecar-{target_triple}"
    if target_platform == "windows":
        binary_name += ".exe"
        
    print(f"Target platform: {target_platform}")
    print(f"Target Triple: {target_triple}")
    print(f"Binary Name: {binary_name}")
    
    # Get ffmpeg for the target platform
    ffmpeg_path = get_ffmpeg_path(target_platform)
    print(f"Using ffmpeg: {ffmpeg_path}")

    # Verify ffmpeg file exists and get its size
    if not os.path.exists(ffmpeg_path):
        print(f"ERROR: ffmpeg file does not exist: {ffmpeg_path}")
        sys.exit(1)

    ffmpeg_size = os.path.getsize(ffmpeg_path)
    print(f"ffmpeg file size: {ffmpeg_size:,} bytes ({ffmpeg_size / 1024 / 1024:.2f} MB)")

    if ffmpeg_size < 1024 * 1024:  # Less than 1 MB is suspicious
        print(f"WARNING: ffmpeg file seems too small ({ffmpeg_size} bytes)")

    # Clean build/dist in src-python
    shutil.rmtree(script_dir / "build", ignore_errors=True)
    shutil.rmtree(script_dir / "dist", ignore_errors=True)

    # PyInstaller arguments
    # IMPORTANT: Always use ; for --add-binary separator on Windows host
    # Use : for Unix hosts (even when building for Windows target)
    separator = ";" if platform.system().lower() == "windows" else ":"
    
    args = [
        "pyinstaller",
        "--onefile",
        "--name", binary_name,
        "--clean",
        "--noconfirm",
        f"--add-binary={ffmpeg_path}{separator}.",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        # Pydantic imports (required for FastAPI on Windows)
        "--hidden-import=pydantic",
        "--hidden-import=pydantic.fields",
        "--hidden-import=pydantic_core",
        # yt-dlp with all dependencies
        "--collect-all=yt_dlp",
        str(script_dir / "main.py")
    ]
    
    print("\nRunning PyInstaller...")
    subprocess.run(args, check=True, cwd=script_dir)

    # Copy binary to src-tauri/binaries
    source_binary = script_dir / "dist" / binary_name
    dest_binary = output_dir / binary_name

    # Verify source binary exists
    if not source_binary.exists():
        print(f"\nERROR: PyInstaller did not create expected binary: {source_binary}")
        print("Build failed!")
        sys.exit(1)

    source_size = source_binary.stat().st_size
    print(f"\nBuilt binary size: {source_size:,} bytes ({source_size / 1024 / 1024:.2f} MB)")

    # Sanity check: binary should be reasonably sized (at least 10 MB)
    if source_size < 10 * 1024 * 1024:
        print(f"WARNING: Binary seems too small ({source_size / 1024 / 1024:.2f} MB)")
        print("This might indicate ffmpeg or other dependencies were not bundled correctly")

    print(f"\nCopying {source_binary} to {dest_binary}...")
    shutil.copy2(source_binary, dest_binary)

    # On Unix, ensure executable
    if platform.system().lower() != "windows":
        st = os.stat(dest_binary)
        os.chmod(dest_binary, st.st_mode | 0o111)

    # Try to verify ffmpeg was included in the bundle (optional check)
    if target_platform == "windows":
        print("\nVerifying Windows binary packaging...")
        # For Windows, we can't easily check without running, so just document
        print("Note: Run the binary and check stderr logs for ffmpeg detection")
        print("Expected log: '[ffmpeg] ✓ Found bundled ffmpeg.exe'")

    print("\n" + "="*60)
    print("✓ Build complete!")
    print("="*60)
    print(f"Sidecar location: {dest_binary}")
    print(f"Sidecar size: {dest_binary.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"ffmpeg bundled from: {ffmpeg_path}")
    print(f"ffmpeg size: {ffmpeg_size / 1024 / 1024:.2f} MB")
    print("\nTo verify ffmpeg was bundled correctly:")
    print("  Run the sidecar and check logs for:")
    print("  '[ffmpeg] ✓ Found bundled ffmpeg'")
    print("="*60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build VideoNote Python Sidecar")
    parser.add_argument(
        "--platform",
        choices=["windows", "darwin", "linux"],
        help="Target platform (defaults to current platform)"
    )
    args = parser.parse_args()
    
    build_sidecar(args.platform)

