# 构建指南 (Build Guide)

本文档说明如何在不同平台上构建 VideoNote，特别是如何确保 ffmpeg 被正确打包到 Windows 版本中。

## 快速开始

### macOS / Linux

```bash
# 1. 安装依赖
npm install
cd src-python
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. 构建 Python Sidecar
python build_sidecar.py

# 3. 构建 Tauri 应用
cd ..
npm run tauri:build
```

### Windows

```bash
# 1. 安装依赖
npm install
cd src-python
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. 构建 Python Sidecar (会自动下载并打包 ffmpeg)
python build_sidecar.py

# 3. 构建 Tauri 应用
cd ..
npm run tauri:build
```

## FFmpeg 打包详解

### 问题背景

Windows 用户可能遇到错误：
```
Download failed: ERROR: You have requested merging of multiple formats but ffmpeg is not installed
```

这是因为 yt-dlp 需要 ffmpeg 来合并视频和音频流。

### 解决方案

构建脚本 `build_sidecar.py` 会自动：

1. **下载 ffmpeg**：如果不存在，自动从 GitHub 下载 Windows 版本的 ffmpeg
2. **打包 ffmpeg**：使用 PyInstaller 的 `--add-binary` 将 ffmpeg.exe 打包进 sidecar
3. **验证打包**：检查文件大小确保 ffmpeg 被正确包含

### 验证 ffmpeg 是否被打包

#### 构建时验证

运行 `python build_sidecar.py` 后，你应该看到：

```
==================================================
Getting ffmpeg for platform: windows
==================================================
✓ ffmpeg saved to: src-python/.ffmpeg_cache/windows/ffmpeg.exe
✓ File size: 103,424,512 bytes (98.61 MB)

ffmpeg file size: 103,424,512 bytes (98.61 MB)

Built binary size: 156,234,567 bytes (148.99 MB)

==================================================
✓ Build complete!
==================================================
Sidecar location: ../src-tauri/binaries/vn-sidecar-x86_64-pc-windows-msvc.exe
Sidecar size: 148.99 MB
ffmpeg bundled from: src-python/.ffmpeg_cache/windows/ffmpeg.exe
ffmpeg size: 98.61 MB
```

**关键点**：
- ffmpeg 文件应该 ~100 MB
- 最终 sidecar 应该 ~150 MB（包含 Python + yt-dlp + ffmpeg）
- 如果 sidecar < 50 MB，说明 ffmpeg 没有被打包

#### 运行时验证

当应用启动并尝试下载视频时，检查日志（Tauri DevTools 或控制台）：

✅ **成功**（ffmpeg 已打包）：
```
[ffmpeg] Platform: win32
[ffmpeg] Running from PyInstaller bundle: C:\Users\...\Temp\_MEI123
[ffmpeg] _MEIPASS contains 245 files
[ffmpeg] Found ffmpeg-related files: ['ffmpeg.exe']
[ffmpeg] Checking for bundled ffmpeg at: C:\Users\...\Temp\_MEI123\ffmpeg.exe
[ffmpeg] ✓ Found bundled ffmpeg.exe
[ffmpeg] Configuring yt-dlp with ffmpeg: C:\Users\...\Temp\_MEI123\ffmpeg.exe
```

❌ **失败**（ffmpeg 未打包）：
```
[ffmpeg] Platform: win32
[ffmpeg] Running from PyInstaller bundle: C:\Users\...\Temp\_MEI123
[ffmpeg] _MEIPASS contains 120 files
[ffmpeg] Checking for bundled ffmpeg at: C:\Users\...\Temp\_MEI123\ffmpeg.exe
[ffmpeg] ✗ Bundled ffmpeg.exe not found
[ffmpeg] ✗ ffmpeg not found in system PATH
[ffmpeg] WARNING: ffmpeg not available, downloading pre-merged formats only
```

### 降级策略

即使 ffmpeg 缺失，应用现在也能继续工作：
- **有 ffmpeg**：下载最高质量，可以合并分离的视频/音频流
- **无 ffmpeg**：只下载预合并的格式，质量可能稍低但不会报错

## 常见问题

### Q: 为什么不能在 macOS 上构建 Windows 版本？

A: PyInstaller **不支持真正的交叉编译**。即使你在 macOS 上运行 `python build_sidecar.py --platform windows`，生成的仍然是 macOS 可执行文件，只是准备了 Windows 的 ffmpeg。

正确的做法：
- 在 Windows 机器上手动构建，或
- 使用 GitHub Actions 自动构建（已配置）

### Q: 构建的 sidecar 很小（<50 MB），怎么办？

A: 这说明 ffmpeg 没有被打包。检查：
1. `.ffmpeg_cache/windows/` 目录是否存在 ffmpeg.exe
2. 构建日志中是否有错误
3. 重新运行 `python build_sidecar.py`

手动下载 ffmpeg：
```bash
cd src-python
python download_ffmpeg.py --platform windows
```

### Q: 如何清理并重新构建？

```bash
# 清理缓存
rm -rf src-python/.ffmpeg_cache
rm -rf src-python/build
rm -rf src-python/dist
rm -rf src-tauri/binaries/*

# 重新构建
cd src-python
python build_sidecar.py
```

### Q: GitHub Actions 构建失败怎么办？

检查 `.github/workflows/release.yml`，确保：
1. `Install ffmpeg (Windows)` 步骤成功
2. `Build Python Sidecar (Windows)` 步骤成功
3. 验证步骤显示二进制文件大小合理

## 技术细节

### PyInstaller --add-binary 语法

```bash
--add-binary=<source>;<dest>  # Windows 主机
--add-binary=<source>:<dest>  # Unix 主机
```

**注意**：分隔符取决于**构建机器**的操作系统，不是目标平台。

### ffmpeg 查找顺序

运行时，应用按以下顺序查找 ffmpeg：

1. **PyInstaller bundle** (`sys._MEIPASS`)
   - Windows: `_MEIPASS/ffmpeg.exe`
   - macOS/Linux: `_MEIPASS/ffmpeg`

2. **系统 PATH**
   - 使用 `shutil.which("ffmpeg")`

3. **降级模式**
   - 如果都找不到，使用预合并格式

### ffmpeg 来源

- **Windows**: https://github.com/GyanD/codexffmpeg/releases/download/7.0.2/ffmpeg-7.0.2-essentials_build.zip (~100 MB)
- **macOS**: 从 Homebrew 安装 (`brew install ffmpeg`)
- **Linux**: https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

## 发布流程

### 自动发布（推荐）

```bash
# 打 tag 触发自动构建
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions 会自动：
1. 在 Windows 和 macOS runners 上构建
2. 下载并打包平台特定的 ffmpeg
3. 创建安装包
4. 发布到 GitHub Releases

### 手动发布

```bash
# 在目标平台上
npm install
cd src-python && python build_sidecar.py && cd ..
npm run tauri:build

# 安装包位置：
# Windows: src-tauri/target/release/bundle/msi/*.msi
# macOS: src-tauri/target/release/bundle/dmg/*.dmg
```

## 参考资料

- [PyInstaller 文档](https://pyinstaller.org/en/stable/)
- [Tauri 构建文档](https://tauri.app/v1/guides/building/)
- [yt-dlp ffmpeg 集成](https://github.com/yt-dlp/yt-dlp#dependencies)
