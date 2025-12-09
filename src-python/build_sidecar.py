import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

# 导入自动下载 ffmpeg 的模块
try:
    from download_ffmpeg import get_ffmpeg_path as auto_get_ffmpeg
except ImportError:
    auto_get_ffmpeg = None

def get_ffmpeg_path(target_platform=None):
    """
    获取 ffmpeg 路径，支持自动下载
    
    Args:
        target_platform: 目标平台 (windows/darwin/linux)
    
    Returns:
        ffmpeg 可执行文件的路径
    """
    # 首先尝试自动下载/获取 ffmpeg
    if auto_get_ffmpeg:
        try:
            print("尝试自动获取 ffmpeg...")
            return auto_get_ffmpeg(target_platform)
        except Exception as e:
            print(f"自动获取 ffmpeg 失败: {e}")
            print("回退到系统 PATH 查找...")
    
    # 回退到检查系统 PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        print("\n" + "="*60)
        print("错误: 未找到 ffmpeg")
        print("="*60)
        print("\n请选择以下方式之一安装 ffmpeg:")
        print("\n方式 1: 使用包管理器安装")
        print("  macOS:   brew install ffmpeg")
        print("  Windows: choco install ffmpeg")
        print("  Linux:   sudo apt-get install ffmpeg")
        print("\n方式 2: 使用自动下载脚本")
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
    构建 Python Sidecar
    
    Args:
        target_platform: 目标平台 (windows/darwin/linux)，如果为 None 则为当前平台
    """
    print("================================================")
    print("Building VideoNote Python Sidecar (Python Script)")
    print("================================================")

    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    output_dir = project_root / "src-tauri" / "binaries"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 确定目标平台
    if target_platform:
        print(f"目标平台 (指定): {target_platform}")
        # 将平台名称转换为目标三元组
        platform_map = {
            "windows": "x86_64-pc-windows-msvc",
            "darwin": get_target_triple(),  # 使用当前系统的架构
            "linux": "x86_64-unknown-linux-gnu",
        }
        target_triple = platform_map.get(target_platform, get_target_triple())
    else:
        target_triple = get_target_triple()
        target_platform = platform.system().lower()
    
    binary_name = f"vn-sidecar-{target_triple}"
    if target_platform == "windows":
        binary_name += ".exe"
        
    print(f"目标平台: {target_platform}")
    print(f"Target Triple: {target_triple}")
    print(f"Binary Name: {binary_name}")
    
    # 获取对应平台的 ffmpeg
    ffmpeg_path = get_ffmpeg_path(target_platform)
    print(f"使用 ffmpeg: {ffmpeg_path}")

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
    import argparse
    
    parser = argparse.ArgumentParser(description="构建 VideoNote Python Sidecar")
    parser.add_argument(
        "--platform",
        choices=["windows", "darwin", "linux"],
        help="目标平台 (默认为当前平台)"
    )
    args = parser.parse_args()
    
    build_sidecar(args.platform)

