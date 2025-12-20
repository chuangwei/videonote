# Windows 部署指南

## 问题诊断与修复

### 已修复的问题

#### 1. ✅ 误导性的ERROR日志
**问题**: 所有stderr输出都被标记为ERROR级别,导致用户误以为程序出错
**修复**: 修改了`src-tauri/src/main.rs`,现在只有真正包含错误关键词的输出才会被标记为ERROR

#### 2. ✅ CSP(内容安全策略)限制
**问题**: Windows打包后可能无法连接到localhost:8118的Python后端
**修复**: 在`src-tauri/tauri.conf.json`中添加了CSP配置,明确允许连接到127.0.0.1:8118

### Windows部署步骤

#### 1. 重新构建Python Sidecar

```bash
# 在Windows上运行
cd src-python
python build_sidecar.py
```

这将生成 `src-tauri/binaries/vn-sidecar-x86_64-pc-windows-msvc.exe`

#### 2. 构建Tauri应用

```bash
npm run tauri:build
```

#### 3. 安装位置

构建完成后,安装包位于:
```
src-tauri/target/release/bundle/
```

### 常见问题排查

#### 问题1: Windows防火墙阻止本地连接

**症状**: 
- 日志显示"连接失败"
- Python sidecar运行正常,但前端无法连接

**解决方案**:
1. 运行应用时,Windows防火墙会弹出提示,请点击"允许访问"
2. 如果错过了提示,手动添加防火墙规则:
   - 打开 Windows Defender 防火墙
   - 点击"允许应用通过防火墙"
   - 找到VideoNote,勾选"专用"和"公用"网络

#### 问题2: 杀毒软件阻止

**症状**:
- Python sidecar无法启动
- 日志显示"Failed to spawn Python sidecar"

**解决方案**:
1. 临时禁用杀毒软件测试
2. 将VideoNote安装目录添加到杀毒软件的白名单
3. 对于企业环境,可能需要IT部门添加例外

#### 问题3: 端口被占用

**症状**:
- 日志显示端口8118相关错误

**解决方案**:
检查端口是否被占用:
```cmd
netstat -ano | findstr :8118
```

如果被占用,可以:
- 关闭占用端口的程序
- 或修改代码使用其他端口

### 调试步骤

#### 1. 查看应用日志

应用日志位于:
```
%APPDATA%\VideoNote\logs\
```

或在应用中点击右上角的日志图标查看实时日志

#### 2. 手动测试Python Sidecar

在命令行中手动运行sidecar:
```cmd
cd C:\Users\你的用户名\AppData\Local\VideoNote\
vn-sidecar.exe --port 8118
```

然后在浏览器访问: http://127.0.0.1:8118/health

#### 3. 检查服务连接

在应用运行时,打开浏览器开发者工具(F12),查看Console和Network标签:
- Console: 查看API连接错误
- Network: 查看请求是否成功到达8118端口

### 日志解读

#### 正常的日志输出

以下输出是**正常的**,不是错误:
```
[videonote][INFO] Sidecar: [INIT] Python version: 3.10.11
[videonote][INFO] Sidecar: [INIT] Platform: win32
[videonote][INFO] Sidecar: [INIT] Working directory: ...
[videonote][INFO] Sidecar: [INFO] Server is ready on port 8118
[videonote][INFO] Sidecar stdout: INFO: 127.0.0.1:xxx - "GET /health HTTP/1.1" 200 OK
```

#### 错误的日志输出

以下才是**真正的错误**:
```
[videonote][ERROR] Sidecar stderr: ERROR: ...
[videonote][ERROR] Sidecar stderr: Exception: ...
[videonote][ERROR] Failed to spawn Python sidecar: ...
```

### 性能优化

#### 启动速度

首次启动可能需要10-30秒,这是正常的,因为:
1. Windows需要解压PyInstaller打包的Python运行时
2. Python需要初始化依赖库(FastAPI, yt-dlp等)
3. 后续启动会快一些(如果系统缓存了相关文件)

#### 内存占用

Python sidecar大约占用:
- 基础内存: ~80-120MB
- 下载时: +50-200MB (取决于缓冲区大小)

### 发布检查清单

在发布新版本前,请确保:

- [ ] Python sidecar已使用`build_sidecar.py`重新构建
- [ ] 测试了Windows 10和Windows 11
- [ ] 测试了首次安装场景
- [ ] 测试了防火墙提示和权限
- [ ] 验证了日志输出正常
- [ ] 测试了下载功能端到端流程
- [ ] 检查了安装包大小(<100MB为佳)
- [ ] 更新了版本号(package.json和tauri.conf.json)

### 高级配置

#### 修改默认端口

如果需要修改默认端口(例如避免冲突):

1. 修改 `src-tauri/src/main.rs` 第86行:
```rust
.args(["--port", "8118"])  // 改为其他端口,如9000
```

2. 修改 `src/lib/api.ts` 第6行:
```typescript
private readonly port: number = 8118;  // 改为相同端口
```

3. 修改 `src-tauri/tauri.conf.json` CSP配置:
```json
"connect-src 'self' http://127.0.0.1:8118 ..."  // 改为新端口
```

#### 自定义日志级别

在 `src-python/main.py` 第357行修改:
```python
log_level="info",  // 可改为 "debug" 获取更多日志
```

### 支持与反馈

如果遇到其他问题:
1. 收集日志文件(位于`%APPDATA%\VideoNote\logs\`)
2. 记录复现步骤
3. 提交Issue时附上系统信息:
   - Windows版本
   - 是否有杀毒软件
   - 是否有VPN/代理
   - 防火墙设置

---

**最后更新**: 2025-12-08



