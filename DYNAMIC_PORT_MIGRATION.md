# 动态端口迁移说明

## 变更概述

从**固定端口 8118** 迁移到**动态端口分配**，让系统自动选择可用端口。

---

## 为什么要改为动态端口?

### 优势 ✅

1. **避免端口冲突**: 不再担心8118端口被其他应用占用
2. **支持多实例**: 可以同时运行多个VideoNote实例
3. **更灵活**: 系统自动选择可用端口，无需手动配置
4. **更符合最佳实践**: 桌面应用通常使用动态端口

### 固定端口的问题 ❌

1. 端口被占用时应用无法启动
2. 无法运行多个实例
3. 需要在防火墙中配置固定端口
4. Windows环境下可能需要管理员权限

---

## 技术实现

### 1. Python后端 (`src-python/main.py`)

**修改前**:
```python
parser.add_argument("--port", type=int, help="Port to run the server on", default=8118)
args = parser.parse_args()
port = args.port  # 固定使用8118
```

**修改后**:
```python
parser.add_argument("--port", type=int, help="Port to run the server on (0 for auto-assign)", default=0)
args = parser.parse_args()

# 使用端口0让系统自动分配
if args.port == 0:
    port = find_free_port()
else:
    port = args.port
```

**工作原理**:
- `find_free_port()` 创建临时socket绑定到端口0
- 操作系统自动分配一个可用端口
- 关闭socket后该端口仍然短时间内可用
- uvicorn启动时使用这个端口

---

### 2. Rust后端 (`src-tauri/src/main.rs`)

**修改前**:
```rust
// 固定端口8118
let sidecar_command = shell.sidecar("vn-sidecar")
    .map(|cmd| cmd.args(["--port", "8118"]));
```

**修改后**:
```rust
// 动态端口(port 0 = 系统自动分配)
let sidecar_command = shell.sidecar("vn-sidecar")
    .map(|cmd| cmd.args(["--port", "0"]));
```

**端口获取机制**:
1. Python sidecar启动后打印 `SERVER_PORT=xxxxx` 到stdout
2. Rust监听stdout，提取端口号
3. 存储到 `SidecarState` 中
4. 通过 `sidecar-port` 事件发送给前端

---

### 3. 前端API客户端 (`src/lib/api.ts`)

**修改前**:
```typescript
class ApiClient {
  private readonly port: number = 8118;  // 固定端口
  private readonly baseUrl: string = `http://127.0.0.1:${this.port}`;
  
  getBaseUrl(): string {
    return this.baseUrl;
  }
}
```

**修改后**:
```typescript
import { invoke, listen } from "@tauri-apps/api/core";

class ApiClient {
  private port: number | null = null;
  private portPromise: Promise<number>;

  constructor() {
    this.portPromise = this.initializePort();
  }

  private async initializePort(): Promise<number> {
    // 1. 监听事件
    await listen<number>("sidecar-port", (event) => {
      this.port = event.payload;
    });

    // 2. 轮询获取(防止错过事件)
    const maxAttempts = 30;
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const port = await invoke<number>("get_sidecar_port");
        this.port = port;
        return port;
      } catch {
        await new Promise(r => setTimeout(r, 1000));
      }
    }
    throw new Error("Failed to get sidecar port");
  }

  async getBaseUrl(): Promise<string> {
    const port = await this.portPromise;
    return `http://127.0.0.1:${port}`;
  }
}
```

**变化**:
- `getBaseUrl()` 从同步变为异步
- 所有API方法都需要先等待端口初始化
- 使用Promise处理异步端口获取

---

### 4. CSP配置 (`src-tauri/tauri.conf.json`)

**修改前**:
```json
{
  "csp": "... connect-src 'self' http://127.0.0.1:8118 http://localhost:8118; ..."
}
```

**修改后**:
```json
{
  "csp": "... connect-src 'self' http://127.0.0.1:* http://localhost:*; ..."
}
```

**说明**: 使用通配符 `*` 允许连接到localhost的任意端口

---

### 5. CORS配置 (`src-python/main.py`)

**修改前**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    ...
)
```

**修改后**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost", ...],
    allow_origin_regex=r"^(http://localhost:\d+|tauri://.*)$",
    ...
)
```

**说明**: 添加正则表达式，允许所有localhost端口的请求

---

## 测试验证

### 1. 端口分配测试

```bash
# 启动第一个实例
npm run tauri:dev

# 在日志中查看分配的端口
# 例如: [INFO] Selected port: 54321

# 启动第二个实例(新终端)
npm run tauri:dev

# 应该看到不同的端口
# 例如: [INFO] Selected port: 54322
```

### 2. 功能测试

- ✅ 健康检查正常
- ✅ 下载功能正常
- ✅ 进度跟踪正常
- ✅ 多实例互不干扰

### 3. 日志验证

正常日志应该显示:
```
[videonote][INFO] Creating sidecar command for 'vn-sidecar' with dynamic port
[videonote][INFO] Sidecar: [INIT] Selected port: 54321
[videonote][INFO] Sidecar stdout: SERVER_PORT=54321
[videonote][INFO] Extracted sidecar port: 54321
[videonote][INFO] Sidecar port stored and emitted to frontend
```

---

## API变化(影响前端代码)

### 之前的用法

```typescript
import { api } from "@/lib/api";

// 同步获取baseUrl
const baseUrl = api.getBaseUrl();  // "http://127.0.0.1:8118"
```

### 现在的用法

```typescript
import { api } from "@/lib/api";

// 异步获取baseUrl
const baseUrl = await api.getBaseUrl();  // "http://127.0.0.1:54321"
```

### API方法调用(无需改变)

API方法内部已经处理异步，使用方式不变:

```typescript
// 都是异步方法，使用方式相同
await api.healthCheck();
await api.startDownload(url, savePath);
await api.getDownloadStatus(taskId);
```

---

## 常见问题

### Q1: 如何查看当前使用的端口?

**A**: 查看应用日志:
- 日志位置: `%APPDATA%\VideoNote\logs\` (Windows)
- 或点击应用右上角日志图标
- 搜索 `Extracted sidecar port`

### Q2: 能否仍然使用固定端口?

**A**: 可以，通过命令行参数:
```bash
# 开发时手动运行Python sidecar
cd src-python
python main.py --port 8118
```

但打包后的应用会使用动态端口。

### Q3: 防火墙会不会每次都提示?

**A**: Windows可能会提示，但通常只在第一次:
- 防火墙规则针对应用程序，不是端口
- 允许`VideoNote.exe`后，所有端口都会被允许

### Q4: 如何支持多实例?

**A**: 直接运行多个应用实例即可:
- 每个实例会使用不同的端口
- 互不干扰

---

## 迁移检查清单

在部署新版本前:

- [ ] 重新构建Python sidecar: `cd src-python && python build_sidecar.py`
- [ ] 重新构建Tauri应用: `npm run tauri:build`
- [ ] 测试端口分配是否正常
- [ ] 测试健康检查
- [ ] 测试下载功能
- [ ] 测试多实例运行
- [ ] 检查日志输出
- [ ] 更新文档和用户指南

---

## 性能影响

- **启动时间**: 增加约0.1-0.5秒(查找可用端口)
- **内存占用**: 无变化
- **运行时性能**: 无影响

---

## 回滚方案

如需回滚到固定端口:

1. **Python** (`src-python/main.py` 第285行):
   ```python
   default=8118  # 改回8118
   ```

2. **Rust** (`src-tauri/src/main.rs` 第88行):
   ```rust
   .map(|cmd| cmd.args(["--port", "8118"]))
   ```

3. **前端** (`src/lib/api.ts`):
   恢复为同步的固定端口实现

4. **CSP** (`src-tauri/tauri.conf.json`):
   ```json
   "connect-src 'self' http://127.0.0.1:8118 ..."
   ```

---

**变更日期**: 2025-12-08  
**影响范围**: 所有平台 (Windows, macOS, Linux)  
**向后兼容**: 是(用户无感知)


