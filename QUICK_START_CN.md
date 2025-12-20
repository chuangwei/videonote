# VideoNote 快速开始指南 🚀

## 🎉 新功能: 自动打包 ffmpeg

现在构建 Windows 应用时，**不需要手动安装 ffmpeg**！构建脚本会自动下载并打包。

## 📦 构建 Windows 应用

### 方式 1: 完全自动 (推荐)

```bash
# 1. 安装 Python 依赖
cd src-python
pip install -r requirements.txt

# 2. 构建 Python Sidecar (自动下载 ffmpeg)
python build_sidecar.py --platform windows

# 3. 安装前端依赖并构建
cd ..
npm install
npm run tauri:build
```

构建完成！安装包在 `src-tauri/target/release/bundle/`

### 方式 2: 先下载 ffmpeg，再构建

如果网络不稳定，可以先单独下载 ffmpeg：

```bash
cd src-python

# 下载 Windows 版本的 ffmpeg
python download_ffmpeg.py --platform windows

# 然后构建
python build_sidecar.py --platform windows
```

### 方式 3: 使用系统安装的 ffmpeg

如果你已经安装了 ffmpeg：

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

## 🧪 测试 ffmpeg 下载

运行测试脚本验证功能：

```bash
cd src-python
python test_ffmpeg_download.py
```

这会：
- ✅ 测试当前平台的 ffmpeg 获取
- ✅ 测试跨平台下载（如果在 macOS 上会测试下载 Windows 版本）
- ✅ 显示缓存状态

## 📂 文件位置

### 构建输出
- **Python Sidecar**: `src-tauri/binaries/vn-sidecar-*.exe`
- **安装包**: `src-tauri/target/release/bundle/`

### ffmpeg 缓存
- **位置**: `src-python/.ffmpeg_cache/`
- **结构**:
  ```
  .ffmpeg_cache/
  ├── windows/
  │   └── ffmpeg.exe        (~80 MB)
  ├── darwin/
  │   └── ffmpeg            (~100 MB)
  └── linux/
      └── ffmpeg            (~90 MB)
  ```

缓存会被 `.gitignore` 忽略，不会提交到 Git。

## 🔍 工作原理

1. **构建时**: 
   - `build_sidecar.py` 调用 `download_ffmpeg.py`
   - 自动检测目标平台
   - 下载对应平台的 ffmpeg（如果缓存中没有）
   - PyInstaller 使用 `--add-binary` 将 ffmpeg 打包进可执行文件

2. **运行时**:
   - Python sidecar 从 PyInstaller 临时目录 (`sys._MEIPASS`) 查找 ffmpeg
   - 如果找不到，回退到系统 PATH
   - yt-dlp 使用 ffmpeg 进行视频格式转换

## 🌍 跨平台支持

| 平台 | 自动下载 | 打包 | 说明 |
|------|---------|------|------|
| Windows | ✅ | ✅ | 自动下载并打包 |
| macOS | ⚠️ | ✅ | 使用系统安装的 ffmpeg |
| Linux | ✅ | ✅ | 自动下载并打包 |

**注意**: macOS 需要先安装 ffmpeg：`brew install ffmpeg`

## ⚠️ 重要提示

### PyInstaller 跨平台限制

虽然我们可以下载任何平台的 ffmpeg，但 **PyInstaller 只能在对应平台上生成可执行文件**：

- 要生成 Windows `.exe` → 必须在 Windows 上运行
- 要生成 macOS 应用 → 必须在 macOS 上运行  
- 要生成 Linux 应用 → 必须在 Linux 上运行

### 推荐方案

使用 **GitHub Actions** 进行多平台构建（已配置在 `.github/workflows/release.yml`）：

```bash
# 创建新版本
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions 会自动在 Windows 和 macOS 上构建
```

## 🐛 常见问题

### 1. 下载 ffmpeg 失败

**症状**:
```
❌ 获取 ffmpeg 失败: HTTP Error 404
```

**解决方案**:
- 检查网络连接
- 使用代理（如果在国内）
- 手动下载 ffmpeg 并放到 `.ffmpeg_cache/windows/`

### 2. 找不到 ffmpeg

**症状**:
```
Error: ffmpeg not found in PATH
```

**解决方案**:
```bash
# 先下载
python download_ffmpeg.py --platform windows

# 或安装到系统
choco install ffmpeg  # Windows
brew install ffmpeg   # macOS
```

### 3. 缓存占用空间太大

每个平台的 ffmpeg 约 80-100 MB。如果不需要，可以删除：

```bash
# 删除所有缓存
rm -rf src-python/.ffmpeg_cache

# 或删除特定平台
rm -rf src-python/.ffmpeg_cache/windows
```

下次构建时会重新下载。

## 📖 更多文档

- [WINDOWS_BUILD_GUIDE.md](./WINDOWS_BUILD_GUIDE.md) - 详细的 Windows 构建指南
- [WINDOWS_DEPLOYMENT.md](./WINDOWS_DEPLOYMENT.md) - Windows 部署和故障排除
- [WINDOWS_FIXES.md](./WINDOWS_FIXES.md) - Windows 修复说明
- [README.md](./README.md) - 完整项目文档

## 🎯 下一步

构建完成后：

1. 在 Windows 上安装应用
2. 首次运行会提示防火墙权限 - 选择"允许"
3. 等待 10-30 秒让 Python sidecar 启动
4. 开始下载视频！

---

**更新日期**: 2025-12-09
**功能状态**: ✅ 已测试并可用




