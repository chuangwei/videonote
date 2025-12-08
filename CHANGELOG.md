# Changelog

All notable changes to VideoNote will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed - Windows Deployment Issues (2025-12-08)

#### 修复了误导性的ERROR日志 🔧
**问题描述**:
在Windows打包后的应用中,所有Python sidecar的stderr输出都被标记为ERROR级别,导致用户看到大量"错误"信息,误以为程序运行失败。实际上这些只是正常的信息输出。

**根本原因**:
`src-tauri/src/main.rs`中对所有stderr输出都使用了`error!`宏记录日志。

**修复方案**:
修改日志记录逻辑,只有真正包含错误关键词("error", "failed", "exception")的输出才会被标记为ERROR级别,其他输出使用INFO级别。

**影响文件**:
- `src-tauri/src/main.rs` (第127-136行)

**示例**:
修复前:
```
[videonote][ERROR] Sidecar stderr: [INIT] Python version: 3.10.11
[videonote][ERROR] Sidecar stderr: [INFO] Server is ready on port 8118
```

修复后:
```
[videonote][INFO] Sidecar: [INIT] Python version: 3.10.11
[videonote][INFO] Sidecar: [INFO] Server is ready on port 8118
```

#### 修复了CSP导致的连接失败 🔧
**问题描述**:
Windows打包后,前端无法通过fetch API连接到localhost:8118的Python后端,导致健康检查失败,应用无法正常使用。

**根本原因**:
Tauri的Content Security Policy (CSP)配置为`null`,在某些Windows环境下会限制对localhost的fetch请求。

**修复方案**:
在`src-tauri/tauri.conf.json`中明确配置CSP,允许连接到127.0.0.1:8118和localhost:8118。

**影响文件**:
- `src-tauri/tauri.conf.json` (第21-26行)

**新增配置**:
```json
"security": {
  "csp": "default-src 'self'; connect-src 'self' http://127.0.0.1:8118 http://localhost:8118; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
  "assetProtocol": {
    "enable": true,
    "scope": ["**"]
  }
}
```

### Added - Windows支持工具 📦

#### Windows部署指南
新增 `WINDOWS_DEPLOYMENT.md` 文档,包含:
- 详细的问题诊断步骤
- Windows特定的部署说明
- 常见问题和解决方案
- 防火墙、杀毒软件处理建议
- 日志解读指南
- 性能优化建议
- 发布前检查清单

#### PowerShell故障排查脚本
新增 `troubleshoot.ps1` 自动诊断脚本,功能包括:
- ✅ 检查Windows版本和系统信息
- ✅ 检查端口8118占用情况
- ✅ 检查防火墙规则
- ✅ 验证应用安装
- ✅ 检查日志文件
- ✅ 测试网络连接
- ✅ 检测安全软件

使用方法:
```powershell
.\troubleshoot.ps1
```

### Technical Details

#### 修改的文件清单:
1. `src-tauri/src/main.rs` - 改进stderr日志级别判断
2. `src-tauri/tauri.conf.json` - 添加CSP配置
3. `README.md` - 添加Windows部署说明
4. `WINDOWS_DEPLOYMENT.md` - 新文件
5. `troubleshoot.ps1` - 新文件
6. `CHANGELOG.md` - 新文件

#### 兼容性测试:
- ✅ Windows 10 (64-bit)
- ✅ Windows 11 (64-bit)
- ✅ macOS (Apple Silicon & Intel)
- ⏳ Linux (未广泛测试)

#### 性能影响:
- 无性能影响
- 日志输出更加清晰准确
- 网络连接更加稳定

### Migration Guide

如果您已经安装了旧版本:

1. **卸载旧版本**:
   - 通过Windows设置卸载VideoNote
   - 或使用安装程序的卸载功能

2. **安装新版本**:
   - 运行新的安装程序
   - 首次启动时允许防火墙访问

3. **验证修复**:
   - 查看日志,应该看到更少的ERROR级别日志
   - 应用应该能够成功连接到Python后端
   - 健康检查应该在10-30秒内通过

### Known Issues

暂无已知问题。如果遇到问题,请:
1. 运行 `troubleshoot.ps1` 诊断
2. 查看 `WINDOWS_DEPLOYMENT.md`
3. 提交Issue并附上诊断结果

---

## [0.1.0] - 2025-12 (Initial Release)

### Added
- 🎉 初始版本发布
- ✅ Tauri v2 + React + TypeScript 前端
- ✅ Python FastAPI sidecar后端
- ✅ yt-dlp视频下载功能
- ✅ 实时进度跟踪
- ✅ Shadcn/UI组件库
- ✅ macOS支持
- ✅ 自动端口发现机制
- ✅ 健康检查和重试逻辑

### Technical Stack
- Frontend: React 19 + TypeScript + Vite
- Desktop: Tauri v2
- Backend: Python 3.10+ + FastAPI + Uvicorn
- Video: yt-dlp + ffmpeg
- UI: Tailwind CSS + Shadcn/UI

---

[Unreleased]: https://github.com/yourusername/videonote/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/videonote/releases/tag/v0.1.0
