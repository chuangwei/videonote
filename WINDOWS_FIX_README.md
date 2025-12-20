# Windows修复说明 (2025-12-20)

## 快速摘要

本次修复针对两个Windows构建问题：

1. ✅ **PyInstaller错误被隐藏** - 已修复
2. ⚠️ **ffmpeg打包失败** - 已增强诊断，待Windows环境验证

## 修改内容

### 核心修复

**文件**: `src-python/build_sidecar.py`
- 移除stdout/stderr捕获，PyInstaller错误现在直接显示
- 添加Windows ffmpeg大小验证（必须>50MB）
- 添加详细的错误调试信息
- 添加PyInstaller归档验证（使用pyi-archive_viewer）

### 新增工具

1. **test_windows_build.ps1** - Windows自动化验证脚本
   ```powershell
   # 快速检查ffmpeg
   .\test_windows_build.ps1 -QuickCheck

   # 完整构建和验证
   .\test_windows_build.ps1 -FullBuild
   ```

2. **WINDOWS_DEBUG_GUIDE.md** - 详细的调试步骤和故障排除

3. **WINDOWS_FIX_FINAL.md** - 完整的修复总结和技术细节

### 更新文档

- **CLAUDE.md** - 添加了Windows调试章节

## 快速开始

### 在Windows上测试

```powershell
# 1. 验证当前状态
.\test_windows_build.ps1 -QuickCheck

# 2. 完整构建
cd src-python
python build_sidecar.py
cd ..

# 3. 验证构建结果
.\test_windows_build.ps1

# 4. 构建Tauri应用
npm run tauri:build
```

### 成功的标志

✅ ffmpeg.exe: ~100 MB
✅ PyInstaller无错误
✅ .spec文件包含ffmpeg
✅ Sidecar二进制: ~150 MB
✅ 运行时日志: `[ffmpeg] OK Found bundled ffmpeg.exe`

## 问题诊断

如果构建失败或ffmpeg未打包：

1. **运行测试脚本**: `.\test_windows_build.ps1 -FullBuild`
2. **查看详细指南**: 打开 `WINDOWS_DEBUG_GUIDE.md`
3. **检查构建日志**: 现在会显示完整的PyInstaller输出
4. **手动测试sidecar**:
   ```powershell
   .\src-tauri\binaries\vn-sidecar-x86_64-pc-windows-msvc.exe --port 8888
   ```

## 关键文件

| 文件 | 用途 |
|------|------|
| `test_windows_build.ps1` | 自动化验证脚本 |
| `WINDOWS_DEBUG_GUIDE.md` | 详细调试指南 |
| `WINDOWS_FIX_FINAL.md` | 完整技术总结 |
| `src-python/build_sidecar.py` | 增强的构建脚本 |

## 下一步

- [ ] 在Windows机器上运行完整测试
- [ ] 验证GitHub Actions构建
- [ ] 测试视频下载功能
- [ ] 确认ffmpeg正确打包

## 获取帮助

详细信息请参考：
- 快速诊断: `.\test_windows_build.ps1 -FullBuild`
- 详细步骤: `WINDOWS_DEBUG_GUIDE.md`
- 技术细节: `WINDOWS_FIX_FINAL.md`
