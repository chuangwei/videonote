# Windows 构建指南 - 自动打包 ffmpeg

本指南说明如何在任何平台上为 Windows 构建 VideoNote 应用，并自动打包 ffmpeg 依赖。

## 🎯 新功能

现在构建脚本支持**自动下载和打包 ffmpeg**，无需手动安装！

## 📋 前提条件

1. Python 3.10+
2. Node.js 20+
3. Rust 工具链

## 🚀 构建步骤

### 方式 1: 自动下载 ffmpeg（推荐）

构建脚本会自动下载对应平台的 ffmpeg：

```bash
# 在 macOS/Linux 上为 Windows 构建
cd src-python
python build_sidecar.py --platform windows

# 为当前平台构建（自动检测）
python build_sidecar.py

# 为 Linux 构建
python build_sidecar.py --platform linux
```

### 方式 2: 手动下载 ffmpeg

如果自动下载失败，可以手动下载：

```bash
# 下载 Windows 版本的 ffmpeg
cd src-python
python download_ffmpeg.py --platform windows

# 然后构建
python build_sidecar.py --platform windows
```

### 方式 3: 使用系统安装的 ffmpeg

如果你的系统已经安装了 ffmpeg：

```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# 然后直接构建
cd src-python
python build_sidecar.py
```

## 📁 文件结构

构建完成后，文件将保存在：

```
src-tauri/binaries/
├── vn-sidecar-x86_64-pc-windows-msvc.exe  # Windows
├── vn-sidecar-aarch64-apple-darwin        # macOS ARM
├── vn-sidecar-x86_64-apple-darwin         # macOS Intel
└── vn-sidecar-x86_64-unknown-linux-gnu    # Linux
```

ffmpeg 缓存在：

```
src-python/.ffmpeg_cache/
├── windows/
│   └── ffmpeg.exe
├── darwin/
│   └── ffmpeg
└── linux/
    └── ffmpeg
```

## 🔧 工作原理

1. **自动下载**: `download_ffmpeg.py` 从官方源下载 ffmpeg：
   - Windows: https://www.gyan.dev/ffmpeg/builds/
   - Linux: https://johnvansickle.com/ffmpeg/
   - macOS: 使用系统安装的 ffmpeg

2. **缓存**: 下载的 ffmpeg 保存在 `.ffmpeg_cache/` 目录，避免重复下载

3. **打包**: PyInstaller 使用 `--add-binary` 将 ffmpeg 打包到可执行文件中

4. **运行时检测**: 应用运行时会自动从以下位置查找 ffmpeg：
   - PyInstaller 临时目录（`sys._MEIPASS`）
   - 系统 PATH

## 🐛 故障排除

### 问题 1: 下载 ffmpeg 失败

**症状**: 
```
❌ 获取 ffmpeg 失败: HTTP Error 404
```

**解决方案**:
1. 检查网络连接
2. 如果在国内，可能需要使用代理：
   ```bash
   export http_proxy=http://127.0.0.1:7890
   export https_proxy=http://127.0.0.1:7890
   python download_ffmpeg.py --platform windows
   ```
3. 或者手动下载 ffmpeg 并放置到 `.ffmpeg_cache/windows/ffmpeg.exe`

### 问题 2: PyInstaller 找不到 ffmpeg

**症状**:
```
Error: ffmpeg not found in PATH
```

**解决方案**:
确保先运行 `download_ffmpeg.py` 或安装系统 ffmpeg：
```bash
python download_ffmpeg.py --platform windows
```

### 问题 3: 跨平台构建限制

**注意**: 虽然我们可以为 Windows 下载 ffmpeg 并打包，但 PyInstaller 本身有跨平台限制：
- **要生成 Windows .exe，需要在 Windows 上运行 PyInstaller**
- **要生成 macOS 二进制，需要在 macOS 上运行**
- **要生成 Linux 二进制，需要在 Linux 上运行**

这是 PyInstaller 的限制，不是我们的脚本限制。

**推荐方案**:
使用 GitHub Actions 进行多平台构建（已配置在 `.github/workflows/release.yml`）

## 🤖 CI/CD 构建

GitHub Actions 工作流已配置为自动：
1. 在 Windows 和 macOS 上运行
2. 安装对应平台的 ffmpeg
3. 构建 Python sidecar
4. 打包 Tauri 应用
5. 创建发布

触发构建：
```bash
git tag v1.0.0
git push origin v1.0.0
```

## ✅ 验证构建

构建完成后，验证 ffmpeg 是否已打包：

### Windows
```cmd
cd src-tauri\target\release
.\vn-sidecar-x86_64-pc-windows-msvc.exe --help
```

### macOS/Linux
```bash
cd src-tauri/target/release
./vn-sidecar-aarch64-apple-darwin --help
```

如果启动成功并显示帮助信息，说明构建成功。

## 📝 手动下载 ffmpeg（备选方案）

如果自动下载不工作，可以手动下载：

### Windows
1. 访问: https://www.gyan.dev/ffmpeg/builds/
2. 下载 `ffmpeg-release-essentials.zip`
3. 解压并找到 `ffmpeg.exe`
4. 复制到 `src-python/.ffmpeg_cache/windows/ffmpeg.exe`

### Linux
1. 访问: https://johnvansickle.com/ffmpeg/
2. 下载静态构建版本
3. 解压并找到 `ffmpeg`
4. 复制到 `src-python/.ffmpeg_cache/linux/ffmpeg`

### macOS
```bash
brew install ffmpeg
```

## 🎉 完成

现在你可以：
- ✅ 在任何平台上构建（受 PyInstaller 限制）
- ✅ 自动下载和打包 ffmpeg
- ✅ 无需手动安装依赖
- ✅ 缓存复用，加快后续构建

## 📚 相关文档

- [WINDOWS_DEPLOYMENT.md](./WINDOWS_DEPLOYMENT.md) - Windows 部署指南
- [WINDOWS_FIXES.md](./WINDOWS_FIXES.md) - Windows 修复说明
- [src-python/README.md](./src-python/README.md) - Python 后端文档

---

**最后更新**: 2025-12-09


