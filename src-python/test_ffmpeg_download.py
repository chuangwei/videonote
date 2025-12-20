#!/usr/bin/env python3
"""
测试 ffmpeg 自动下载功能
"""

import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from download_ffmpeg import get_ffmpeg_path


def test_current_platform():
    """测试当前平台的 ffmpeg 下载"""
    print("\n" + "=" * 60)
    print("测试 1: 获取当前平台的 ffmpeg")
    print("=" * 60)
    
    try:
        ffmpeg_path = get_ffmpeg_path()
        print(f"✅ 成功! ffmpeg 路径: {ffmpeg_path}")
        
        # 验证文件存在
        if Path(ffmpeg_path).exists():
            file_size = Path(ffmpeg_path).stat().st_size / (1024 * 1024)
            print(f"✅ 文件存在，大小: {file_size:.2f} MB")
        else:
            print(f"❌ 文件不存在: {ffmpeg_path}")
            
    except Exception as e:
        print(f"❌ 失败: {e}")


def test_windows_platform():
    """测试 Windows 平台的 ffmpeg 下载"""
    print("\n" + "=" * 60)
    print("测试 2: 下载 Windows 平台的 ffmpeg")
    print("=" * 60)
    
    try:
        ffmpeg_path = get_ffmpeg_path("windows")
        print(f"✅ 成功! Windows ffmpeg 路径: {ffmpeg_path}")
        
        # 验证文件存在
        if Path(ffmpeg_path).exists():
            file_size = Path(ffmpeg_path).stat().st_size / (1024 * 1024)
            print(f"✅ 文件存在，大小: {file_size:.2f} MB")
            
            # 检查是否是 .exe 文件
            if ffmpeg_path.endswith('.exe'):
                print(f"✅ 正确的 Windows 可执行文件格式")
            else:
                print(f"⚠️  警告: 文件不是 .exe 格式")
        else:
            print(f"❌ 文件不存在: {ffmpeg_path}")
            
    except Exception as e:
        print(f"❌ 失败: {e}")


def show_cache_status():
    """显示缓存状态"""
    print("\n" + "=" * 60)
    print("缓存状态")
    print("=" * 60)
    
    cache_dir = Path(__file__).parent / ".ffmpeg_cache"
    
    if not cache_dir.exists():
        print("❌ 缓存目录不存在")
        return
    
    for platform_dir in cache_dir.iterdir():
        if platform_dir.is_dir():
            print(f"\n平台: {platform_dir.name}")
            for file in platform_dir.iterdir():
                if file.is_file():
                    size = file.stat().st_size / (1024 * 1024)
                    print(f"  ✅ {file.name} ({size:.2f} MB)")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("VideoNote - ffmpeg 自动下载功能测试")
    print("=" * 60)
    
    # 测试当前平台
    test_current_platform()
    
    # 测试 Windows 平台 (如果不在 Windows 上)
    import platform
    if platform.system().lower() != "windows":
        print("\n提示: 正在测试跨平台下载 (下载 Windows 版本的 ffmpeg)")
        test_windows_platform()
    
    # 显示缓存状态
    show_cache_status()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)




