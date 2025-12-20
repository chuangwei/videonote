# VideoNote - 自动 ffmpeg 打包功能演示脚本

## 🎬 演示场景

展示如何在 macOS 上为 Windows 构建应用，自动下载并打包 ffmpeg。

## 📝 演示步骤

### 第一步：准备工作

```bash
# 克隆项目（或进入项目目录）
cd /path/to/videonote

# 安装 Python 依赖
cd src-python
pip install -r requirements.txt
```

**说明**: 这是基本的准备工作，确保 Python 环境就绪。

---

### 第二步：测试 ffmpeg 自动下载功能

```bash
# 运行测试脚本
python test_ffmpeg_download.py
```

**预期输出**:
```
============================================================
VideoNote - ffmpeg 自动下载功能测试
============================================================

============================================================
测试 1: 获取当前平台的 ffmpeg
============================================================
尝试自动获取 ffmpeg...
使用系统的 ffmpeg: /opt/homebrew/bin/ffmpeg
✅ 成功! ffmpeg 路径: /path/to/.ffmpeg_cache/darwin/ffmpeg
✅ 文件存在，大小: 102.45 MB

提示: 正在测试跨平台下载 (下载 Windows 版本的 ffmpeg)

============================================================
测试 2: 下载 Windows 平台的 ffmpeg
============================================================
正在下载: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
进度: 15.2% (13245678/87234567 字节)
进度: 45.8% (39876543/87234567 字节)
进度: 78.3% (68234567/87234567 字节)
进度: 100.0% (87234567/87234567 字节)
下载完成!
正在解压: /path/to/.ffmpeg_cache/temp_download/ffmpeg.zip
解压完成!
找到 ffmpeg: /path/to/.../bin/ffmpeg.exe
✅ 成功! Windows ffmpeg 路径: /path/to/.ffmpeg_cache/windows/ffmpeg.exe
✅ 文件存在，大小: 81.23 MB
✅ 正确的 Windows 可执行文件格式

============================================================
缓存状态
============================================================
平台: darwin
  ✅ ffmpeg (102.45 MB)
平台: windows
  ✅ ffmpeg.exe (81.23 MB)

============================================================
测试完成!
============================================================
```

**关键点**:
- ✅ 自动下载 Windows 版本的 ffmpeg
- ✅ 显示下载进度
- ✅ 智能缓存到本地
- ✅ 验证文件完整性

---

### 第三步：查看缓存目录

```bash
# 查看缓存结构
tree .ffmpeg_cache/
# 或
ls -lh .ffmpeg_cache/*/
```

**预期输出**:
```
.ffmpeg_cache/
├── darwin/
│   └── ffmpeg          (102 MB)
└── windows/
    └── ffmpeg.exe      (81 MB)
```

**说明**: ffmpeg 已经下载并缓存，下次构建不需要重新下载。

---

### 第四步：构建 Windows Sidecar

```bash
# 为 Windows 平台构建 (使用缓存的 ffmpeg)
python build_sidecar.py --platform windows
```

**预期输出**:
```
================================================
Building VideoNote Python Sidecar (Python Script)
================================================
目标平台: windows
Target Triple: x86_64-pc-windows-msvc
Binary Name: vn-sidecar-x86_64-pc-windows-msvc.exe

==================================================
获取 ffmpeg 用于平台: windows
==================================================
尝试自动获取 ffmpeg...
使用缓存的 ffmpeg: /path/to/.ffmpeg_cache/windows/ffmpeg.exe

✅ ffmpeg 准备就绪: /path/to/.ffmpeg_cache/windows/ffmpeg.exe
使用 ffmpeg: /path/to/.ffmpeg_cache/windows/ffmpeg.exe

运行 PyInstaller...
[PyInstaller 输出...]
INFO: Building EXE from EXE-00.toc completed successfully.

复制 /path/to/dist/vn-sidecar-x86_64-pc-windows-msvc.exe 
到 /path/to/../src-tauri/binaries/vn-sidecar-x86_64-pc-windows-msvc.exe...

构建完成!
Sidecar location: /path/to/../src-tauri/binaries/vn-sidecar-x86_64-pc-windows-msvc.exe
```

**关键点**:
- ✅ 使用缓存的 ffmpeg（无需重新下载）
- ✅ PyInstaller 自动打包 ffmpeg
- ✅ 输出到 src-tauri/binaries/

---

### 第五步：验证构建结果

```bash
# 检查构建的二进制文件
ls -lh ../src-tauri/binaries/
```

**预期输出**:
```
total 140M
-rwxr-xr-x  1 user  staff   65M Dec  9 16:30 vn-sidecar-x86_64-pc-windows-msvc.exe
```

**说明**: 
- ✅ Windows 可执行文件已生成
- ✅ 文件大小约 65MB（包含 Python + 依赖 + ffmpeg）
- ✅ 可以直接在 Windows 上运行

---

### 第六步：构建完整的 Tauri 应用

```bash
# 回到项目根目录
cd ..

# 安装前端依赖（如果还没有）
npm install

# 构建 Tauri 应用
npm run tauri:build
```

**预期输出**:
```
> tauri build

[vite build 输出...]
✓ built in 2.34s

[tauri build 输出...]
    Finished release [optimized] target(s) in 45.67s
    Bundling [bundle name] (/path/to/src-tauri/target/release/bundle/...)
```

**说明**: 
- ✅ Tauri 会自动将 sidecar 打包进应用
- ✅ 生成的安装包包含所有依赖
- ✅ 用户无需安装 ffmpeg

---

## 🎯 演示重点

### 1. 零配置体验
- 不需要手动下载 ffmpeg
- 不需要配置环境变量
- 一条命令自动完成

### 2. 智能缓存
- 首次下载后自动缓存
- 后续构建直接使用缓存
- 加快构建速度

### 3. 跨平台支持
- 在 macOS 上可以为 Windows 准备 ffmpeg
- 支持多平台构建准备
- 统一的构建流程

### 4. 用户友好
- 清晰的进度显示
- 详细的错误提示
- 多种备选方案

---

## 📊 对比演示

### 之前的流程 ❌

```bash
# 1. 安装 ffmpeg（用户需要手动做）
choco install ffmpeg  # Windows
brew install ffmpeg   # macOS

# 2. 确保在 PATH 中（可能需要配置）
which ffmpeg

# 3. 构建
cd src-python
python build_sidecar.py

# 问题：
# - 用户可能不知道如何安装 ffmpeg
# - 版本可能不一致
# - PATH 配置可能出错
# - 支持成本高
```

### 现在的流程 ✅

```bash
# 1. 一条命令，自动完成
cd src-python
python build_sidecar.py --platform windows

# 优势：
# ✅ 自动下载 ffmpeg
# ✅ 版本统一
# ✅ 零配置
# ✅ 智能缓存
```

---

## 🎤 演示话术

### 开场
"大家好，今天我要展示 VideoNote 的新功能：自动 ffmpeg 打包。这个功能解决了 Windows 应用构建时需要手动安装 ffmpeg 的痛点。"

### 测试演示
"首先，让我们运行测试脚本。你会看到它自动检测当前平台，然后下载 Windows 版本的 ffmpeg。注意这里的进度条，下载过程一目了然。"

### 缓存展示
"下载完成后，ffmpeg 被缓存到本地。下次构建时，直接使用缓存，不需要重新下载。让我们看看缓存目录..."

### 构建演示
"现在运行构建命令。注意，这里直接使用了缓存的 ffmpeg，非常快。PyInstaller 会把 ffmpeg 打包进可执行文件。"

### 结果验证
"构建完成！生成的 .exe 文件包含了 Python 运行时、所有依赖库，以及 ffmpeg。用户在 Windows 上运行时，完全不需要安装任何额外软件。"

### 总结
"总结一下：零配置、自动下载、智能缓存、开箱即用。这大大简化了构建流程，提升了用户体验。"

---

## 🔄 常见问题演示

### Q: 如果下载失败怎么办？

```bash
# 方案 1: 重试
python download_ffmpeg.py --platform windows

# 方案 2: 使用系统 ffmpeg
brew install ffmpeg
python build_sidecar.py

# 方案 3: 手动下载并放到缓存目录
# 下载 ffmpeg.exe 并放到 .ffmpeg_cache/windows/
```

### Q: 缓存占用太多空间？

```bash
# 删除特定平台的缓存
rm -rf .ffmpeg_cache/windows

# 或删除所有缓存
rm -rf .ffmpeg_cache
```

### Q: 如何更新 ffmpeg 版本？

```bash
# 删除缓存，下次构建会下载最新版
rm -rf .ffmpeg_cache/windows
python build_sidecar.py --platform windows
```

---

## ✨ 亮点总结

1. **开发者体验**
   - 一条命令完成构建
   - 智能错误处理
   - 清晰的进度反馈

2. **用户体验**
   - 无需安装依赖
   - 开箱即用
   - 零配置

3. **技术亮点**
   - 智能缓存机制
   - 跨平台支持
   - 多种回退方案

4. **文档完善**
   - 详细的构建指南
   - 快速开始文档
   - 故障排除手册

---

**演示时长**: 约 5-10 分钟  
**适用场景**: 技术分享、产品演示、用户培训




