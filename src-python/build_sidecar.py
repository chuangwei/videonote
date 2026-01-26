import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

# Import ffmpeg module
try:
    from download_ffmpeg import get_ffmpeg_path as auto_get_ffmpeg
except ImportError:
    auto_get_ffmpeg = None

def get_ffmpeg_path():
    """
    Get ffmpeg path from Homebrew

    Returns:
        Path to ffmpeg executable
    """
    # Try to auto-get ffmpeg from Homebrew
    if auto_get_ffmpeg:
        try:
            print("Getting ffmpeg from Homebrew...")
            return auto_get_ffmpeg()
        except Exception as e:
            print(f"Auto-get ffmpeg failed: {e}")
            print("Falling back to system PATH search...")

    # Fall back to checking system PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        print("\n" + "="*60)
        print("Error: ffmpeg not found")
        print("="*60)
        print("\nPlease install ffmpeg using Homebrew:")
        print("  brew install ffmpeg")
        print("\n" + "="*60)
        sys.exit(1)

    return ffmpeg_path

def get_target_triple():
    """Get macOS target triple based on architecture"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system != "darwin":
        print(f"Unsupported platform: {system}")
        print("This application only supports macOS")
        sys.exit(1)

    if machine == "arm64":
        return "aarch64-apple-darwin"
    else:
        return "x86_64-apple-darwin"

def build_sidecar():
    """
    Build Python Sidecar for macOS
    """
    print("================================================")
    print("Building VideoNote Python Sidecar for macOS")
    print("================================================")

    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    output_dir = project_root / "src-tauri" / "binaries"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get target triple for current macOS architecture
    target_triple = get_target_triple()
    binary_name = f"vn-sidecar-{target_triple}"

    print(f"Target Triple: {target_triple}")
    print(f"Binary Name: {binary_name}")

    # Get ffmpeg from Homebrew
    ffmpeg_path = get_ffmpeg_path()
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

    # Prepare ffmpeg path for PyInstaller
    ffmpeg_abs_path = str(Path(ffmpeg_path).absolute())

    print(f"\n{'='*60}")
    print("PyInstaller Binary Configuration:")
    print(f"{'='*60}")
    print(f"ffmpeg path: {ffmpeg_abs_path}")
    print(f"{'='*60}\n")

    # PyInstaller arguments for macOS
    args = [
        "pyinstaller",
        "--onefile",
        "--name", binary_name,
        "--clean",
        "--noconfirm",
        "--add-binary", f"{ffmpeg_abs_path}:.",
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
        "--hidden-import=pydantic",
        "--hidden-import=pydantic.fields",
        "--hidden-import=pydantic_core",
        "--collect-all=yt_dlp",
        str(script_dir / "main.py")
    ]

    print("\nRunning PyInstaller...")
    print("Full PyInstaller command:")
    print(" ".join(args))
    print()
    print("="*60)

    try:
        print("Starting PyInstaller build...")
        subprocess.run(args, cwd=script_dir, check=True)
        print("="*60)
        print("PyInstaller completed successfully!")
    except subprocess.CalledProcessError as e:
        print("="*60)
        print(f"\nERROR: PyInstaller failed with exit code {e.returncode}")
        print("\nDebugging information:")
        print(f"  Working directory: {script_dir}")
        print(f"  ffmpeg path: {ffmpeg_abs_path}")
        print(f"  ffmpeg exists: {os.path.exists(ffmpeg_abs_path)}")
        if os.path.exists(ffmpeg_abs_path):
            print(f"  ffmpeg size: {os.path.getsize(ffmpeg_abs_path):,} bytes")
        print(f"  Command: {' '.join(args)}")
        sys.exit(1)

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

    print(f"\nCopying Python sidecar {source_binary} to {dest_binary}...")
    shutil.copy2(source_binary, dest_binary)

    # Set executable permissions
    st = os.stat(dest_binary)
    os.chmod(dest_binary, st.st_mode | 0o111)

    print("\n" + "="*60)
    print("BUILD COMPLETE!")
    print("="*60)
    print(f"\nBuild output:")
    print(f"  Sidecar: {dest_binary}")
    print(f"  Sidecar size: {dest_binary.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"\nNote: ffmpeg is bundled inside the sidecar binary")
    print("="*60)

if __name__ == "__main__":
    build_sidecar()

