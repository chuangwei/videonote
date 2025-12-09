"""
自动下载 ffmpeg 二进制文件用于打包
支持 Windows, macOS, Linux
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
        # 对于 macOS，我们使用系统安装的 ffmpeg
        "url": None,
        "executable": "ffmpeg",
    },
    "linux": {
        "url": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
        "executable": "ffmpeg",
    }
}


def get_platform_key():
    """获取平台标识符"""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        raise Exception(f"不支持的平台: {system}")


def download_file(url, dest_path):
    """下载文件并显示进度"""
    print(f"正在下载: {url}")
    
    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(downloaded * 100.0 / total_size, 100)
            sys.stdout.write(f"\r进度: {percent:.1f}% ({downloaded}/{total_size} 字节)")
            sys.stdout.flush()
    
    urllib.request.urlretrieve(url, dest_path, reporthook)
    print("\n下载完成!")


def extract_zip(zip_path, extract_to):
    """解压 ZIP 文件"""
    print(f"正在解压: {zip_path}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print("解压完成!")


def extract_tar(tar_path, extract_to):
    """解压 TAR 文件"""
    print(f"正在解压: {tar_path}")
    with tarfile.open(tar_path, 'r:*') as tar_ref:
        tar_ref.extractall(extract_to)
    print("解压完成!")


def find_ffmpeg_in_directory(directory, executable_name):
    """在目录中递归查找 ffmpeg 可执行文件"""
    for root, dirs, files in os.walk(directory):
        if executable_name in files:
            return os.path.join(root, executable_name)
    return None


def download_ffmpeg_for_platform(platform_key, cache_dir):
    """
    为指定平台下载 ffmpeg
    
    Args:
        platform_key: 平台标识符 (windows/darwin/linux)
        cache_dir: 缓存目录
    
    Returns:
        ffmpeg 可执行文件的路径
    """
    config = FFMPEG_VERSIONS.get(platform_key)
    if not config:
        raise Exception(f"不支持的平台: {platform_key}")
    
    executable_name = config["executable"]
    
    # 检查是否已经下载过
    cached_ffmpeg = cache_dir / executable_name
    if cached_ffmpeg.exists():
        print(f"使用缓存的 ffmpeg: {cached_ffmpeg}")
        return str(cached_ffmpeg)
    
    # 对于 macOS，尝试使用系统安装的 ffmpeg
    if platform_key == "darwin":
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            print(f"使用系统的 ffmpeg: {system_ffmpeg}")
            # 复制到缓存目录
            shutil.copy2(system_ffmpeg, cached_ffmpeg)
            return str(cached_ffmpeg)
        else:
            raise Exception("macOS 上未找到 ffmpeg，请使用 'brew install ffmpeg' 安装")
    
    url = config.get("url")
    if not url:
        raise Exception(f"平台 {platform_key} 没有配置下载 URL")
    
    # 创建临时下载目录
    download_dir = cache_dir / "temp_download"
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # 确定文件扩展名
    if url.endswith('.zip'):
        archive_path = download_dir / "ffmpeg.zip"
        extract_func = extract_zip
    elif url.endswith('.tar.xz') or url.endswith('.tar.gz'):
        archive_path = download_dir / "ffmpeg.tar.xz"
        extract_func = extract_tar
    else:
        raise Exception(f"不支持的归档格式: {url}")
    
    try:
        # 下载归档文件
        download_file(url, archive_path)
        
        # 解压
        extract_to = download_dir / "extracted"
        extract_to.mkdir(exist_ok=True)
        extract_func(archive_path, extract_to)
        
        # 查找 ffmpeg 可执行文件
        ffmpeg_path = find_ffmpeg_in_directory(extract_to, executable_name)
        if not ffmpeg_path:
            raise Exception(f"在解压的文件中未找到 {executable_name}")
        
        print(f"找到 ffmpeg: {ffmpeg_path}")
        
        # 复制到缓存目录
        shutil.copy2(ffmpeg_path, cached_ffmpeg)
        
        # 在 Unix 系统上设置可执行权限
        if platform_key != "windows":
            os.chmod(cached_ffmpeg, 0o755)
        
        print(f"ffmpeg 已保存到: {cached_ffmpeg}")
        return str(cached_ffmpeg)
        
    finally:
        # 清理临时文件
        if download_dir.exists():
            shutil.rmtree(download_dir)


def get_ffmpeg_path(target_platform=None):
    """
    获取 ffmpeg 路径，如果不存在则自动下载
    
    Args:
        target_platform: 目标平台 (windows/darwin/linux)，如果为 None 则使用当前平台
    
    Returns:
        ffmpeg 可执行文件的路径
    """
    if target_platform is None:
        target_platform = get_platform_key()
    
    # 创建缓存目录
    script_dir = Path(__file__).parent
    cache_dir = script_dir / ".ffmpeg_cache" / target_platform
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*50}")
    print(f"获取 ffmpeg 用于平台: {target_platform}")
    print(f"{'='*50}")
    
    try:
        ffmpeg_path = download_ffmpeg_for_platform(target_platform, cache_dir)
        print(f"\n✅ ffmpeg 准备就绪: {ffmpeg_path}")
        return ffmpeg_path
    except Exception as e:
        print(f"\n❌ 获取 ffmpeg 失败: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="下载 ffmpeg 二进制文件")
    parser.add_argument(
        "--platform",
        choices=["windows", "darwin", "linux"],
        help="目标平台 (默认为当前平台)"
    )
    args = parser.parse_args()
    
    try:
        ffmpeg_path = get_ffmpeg_path(args.platform)
        print(f"\n成功! ffmpeg 路径: {ffmpeg_path}")
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)
