# Windows Build & Debug Guide

## 问题诊断流程

### 问题1: PyInstaller编译错误被隐藏 ✅ 已修复
**状态**: 在最近的提交中已修复 (commit fd91aad)

**修复内容**:
- 移除了 `capture_output=True`，让PyInstaller直接输出到控制台
- 现在可以看到实际的PyInstaller错误信息
- 添加了详细的错误调试信息

### 问题2: Windows上ffmpeg打包失败 ⚠️ 需验证

**症状**:
- Sidecar二进制文件太小 (~50 MB而不是~150 MB)
- 运行时日志显示: `[ffmpeg] NOT FOUND: Bundled ffmpeg.exe not found`
- 视频下载失败并提示需要ffmpeg

**根本原因**:
PyInstaller的`--add-binary`参数在Windows环境下可能由于以下原因失败:
1. 路径中包含空格或特殊字符
2. Windows路径分隔符问题
3. PyInstaller版本兼容性问题

## 调试步骤

### Step 1: 验证ffmpeg下载

```powershell
cd src-python
python download_ffmpeg.py --platform windows

# 检查下载结果
$ffmpegPath = ".ffmpeg_cache/windows/ffmpeg.exe"
if (Test-Path $ffmpegPath) {
    $size = (Get-Item $ffmpegPath).Length / 1MB
    Write-Host "✓ ffmpeg.exe exists: $([math]::Round($size, 2)) MB"
    if ($size -lt 50) {
        Write-Host "ERROR: File too small!" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: ffmpeg.exe not found!" -ForegroundColor Red
}
```

**预期结果**: ffmpeg.exe应该是 ~100 MB

### Step 2: 构建Python Sidecar

```powershell
cd src-python
python build_sidecar.py

# 构建过程应该显示:
# ✓ ffmpeg file size: ~100 MB
# ✓ PyInstaller completed successfully!
# ✓ Sidecar binary size: ~150 MB
```

**关键检查点**:
1. ffmpeg路径是否正确显示
2. PyInstaller是否报错
3. 生成的.spec文件是否包含ffmpeg引用
4. 最终二进制文件大小

### Step 3: 检查.spec文件

```powershell
# 查看生成的.spec文件
$specFile = "vn-sidecar-x86_64-pc-windows-msvc.exe.spec"
if (Test-Path $specFile) {
    Get-Content $specFile | Select-String -Pattern "ffmpeg|binaries|datas"
}
```

**预期输出**: 应该看到类似以下内容:
```python
a.binaries + [('ffmpeg.exe', 'C:\\path\\to\\.ffmpeg_cache\\windows\\ffmpeg.exe', 'BINARY')]
```

### Step 4: 验证Sidecar二进制

```powershell
$binaryPath = "../src-tauri/binaries/vn-sidecar-x86_64-pc-windows-msvc.exe"
if (Test-Path $binaryPath) {
    $size = (Get-Item $binaryPath).Length / 1MB
    Write-Host "Sidecar size: $([math]::Round($size, 2)) MB"

    if ($size -lt 100) {
        Write-Host "ERROR: Binary too small! ffmpeg likely not bundled." -ForegroundColor Red
    } elseif ($size -gt 130 -and $size -lt 180) {
        Write-Host "✓ Size looks correct (~150 MB with ffmpeg)" -ForegroundColor Green
    } else {
        Write-Host "⚠ Unusual size, please verify" -ForegroundColor Yellow
    }
} else {
    Write-Host "ERROR: Sidecar binary not found!" -ForegroundColor Red
}
```

### Step 5: 运行时验证

```powershell
# 手动运行sidecar测试ffmpeg检测
cd ../src-tauri/binaries
./vn-sidecar-x86_64-pc-windows-msvc.exe --port 8888

# 查看stderr输出，应该看到:
# [ffmpeg] Platform: win32
# [ffmpeg] Running from PyInstaller bundle: C:\Users\...\Temp\_MEI...
# [ffmpeg] OK Found bundled ffmpeg.exe    ← 关键!
```

## 常见问题和解决方案

### 问题A: ffmpeg.exe下载失败

**症状**: `download_ffmpeg.py` 报错或下载的文件太小

**解决方案**:
```powershell
# 清除缓存重新下载
Remove-Item -Recurse -Force src-python/.ffmpeg_cache
cd src-python
python download_ffmpeg.py --platform windows

# 如果下载仍然失败，手动下载:
# 1. 访问: https://github.com/GyanD/codexffmpeg/releases/download/7.0.2/ffmpeg-7.0.2-essentials_build.zip
# 2. 解压并复制ffmpeg.exe到: src-python/.ffmpeg_cache/windows/ffmpeg.exe
```

### 问题B: PyInstaller无法找到ffmpeg

**症状**: .spec文件中没有ffmpeg引用，或二进制太小

**可能原因**:
1. ffmpeg路径包含特殊字符
2. PyInstaller版本问题

**解决方案**:
```powershell
# 检查PyInstaller版本
pip show pyinstaller

# 如果版本过旧，升级:
pip install --upgrade pyinstaller

# 重新构建
cd src-python
Remove-Item -Recurse -Force build, dist
python build_sidecar.py
```

### 问题C: --add-binary参数格式错误

**症状**: PyInstaller报错关于binaries参数

**当前实现**:
```python
# build_sidecar.py line 130
separator = ";" if platform.system().lower() == "windows" else ":"
```

Windows使用 `;` 作为分隔符，Unix使用 `:`

**验证**:
```powershell
# 检查build_sidecar.py中的separator逻辑
Select-String -Path "src-python/build_sidecar.py" -Pattern "separator"
```

### 问题D: GitHub Actions构建失败

**调试步骤**:
1. 查看Actions日志中的"Build Python Sidecar (Windows)"步骤
2. 确认ffmpeg下载成功
3. 确认.spec文件包含ffmpeg
4. 确认最终二进制大小

**关键日志检查点**:
```
✓ ffmpeg.exe size: ~100 MB
✓ ffmpeg found in .spec file
✓ Sidecar binary size: ~150 MB
```

## 修复建议

### 如果ffmpeg仍未打包成功

尝试以下替代方案:

#### 方案1: 使用绝对路径（无特殊字符）

```python
# 在build_sidecar.py中临时复制ffmpeg到简单路径
import tempfile
temp_dir = Path(tempfile.gettempdir()) / "videonote_build"
temp_dir.mkdir(exist_ok=True)
temp_ffmpeg = temp_dir / "ffmpeg.exe"
shutil.copy2(ffmpeg_abs_path, temp_ffmpeg)

# 使用临时路径
args.extend(["--add-binary", f"{temp_ffmpeg}{separator}."])
```

#### 方案2: 手动编辑.spec文件

```python
# 1. 先生成.spec文件
subprocess.run([
    "pyinstaller",
    "--onefile",
    "--name", binary_name,
    "main.py"
], cwd=script_dir)

# 2. 修改.spec文件添加ffmpeg
spec_file = script_dir / f"{binary_name}.spec"
with open(spec_file, 'r', encoding='utf-8') as f:
    spec_content = f.read()

# 修改binaries部分
spec_content = spec_content.replace(
    "binaries=[],",
    f"binaries=[('ffmpeg.exe', r'{ffmpeg_abs_path}', 'BINARY')],"
)

with open(spec_file, 'w', encoding='utf-8') as f:
    f.write(spec_content)

# 3. 使用.spec文件构建
subprocess.run(["pyinstaller", str(spec_file)], cwd=script_dir, check=True)
```

#### 方案3: 使用datas而不是binaries

有时候PyInstaller对datas处理更可靠:

```python
args.extend(["--add-data", f"{ffmpeg_abs_path}{separator}."])
```

然后在运行时代码中：
```python
# core/downloader.py
if hasattr(sys, '_MEIPASS'):
    # 尝试从data目录获取
    ffmpeg_path = os.path.join(sys._MEIPASS, "ffmpeg.exe")
```

## 验证清单

构建成功后，确认以下各项:

- [ ] ffmpeg.exe已下载（~100 MB）
- [ ] PyInstaller构建无错误
- [ ] .spec文件包含ffmpeg引用
- [ ] Sidecar二进制~150 MB
- [ ] 手动运行sidecar显示"Found bundled ffmpeg.exe"
- [ ] 下载视频功能正常工作
- [ ] GitHub Actions构建通过

## 参考文件

- `src-python/build_sidecar.py` - 主构建脚本（已增强错误处理）
- `src-python/download_ffmpeg.py` - ffmpeg下载脚本
- `src-python/core/downloader.py` - ffmpeg检测逻辑
- `.github/workflows/release.yml` - CI/CD配置

## 联系支持

如果以上步骤仍无法解决问题，请提供:
1. `build_sidecar.py`的完整输出
2. 生成的.spec文件内容
3. Sidecar二进制文件大小
4. 手动运行sidecar的stderr输出
5. Windows版本和Python版本
