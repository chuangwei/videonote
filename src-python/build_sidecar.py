import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

def get_ffmpeg_path():
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        print("Error: ffmpeg not found in PATH. Please install ffmpeg.")
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

def build_sidecar():
    print("================================================")
    print("Building VideoNote Python Sidecar (Python Script)")
    print("================================================")

    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    output_dir = project_root / "src-tauri" / "binaries"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    target_triple = get_target_triple()
    binary_name = f"vn-sidecar-{target_triple}"
    if platform.system().lower() == "windows":
        binary_name += ".exe"
        
    print(f"Target Triple: {target_triple}")
    print(f"Binary Name: {binary_name}")
    
    ffmpeg_path = get_ffmpeg_path()
    print(f"Found ffmpeg at: {ffmpeg_path}")

    # Clean build/dist in src-python
    shutil.rmtree(script_dir / "build", ignore_errors=True)
    shutil.rmtree(script_dir / "dist", ignore_errors=True)

    # PyInstaller arguments
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
        "--collect-all=yt_dlp",
        str(script_dir / "main.py")
    ]
    
    print("\nRunning PyInstaller...")
    subprocess.run(args, check=True, cwd=script_dir)

    # Copy binary to src-tauri/binaries
    source_binary = script_dir / "dist" / binary_name
    dest_binary = output_dir / binary_name
    
    print(f"\nCopying {source_binary} to {dest_binary}...")
    shutil.copy2(source_binary, dest_binary)

    # On Unix, ensure executable
    if platform.system().lower() != "windows":
        st = os.stat(dest_binary)
        os.chmod(dest_binary, st.st_mode | 0o111)

    print("\nBuild complete!")
    print(f"Sidecar location: {dest_binary}")

if __name__ == "__main__":
    build_sidecar()

