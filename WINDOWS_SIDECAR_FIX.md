# Windows 打包 Sidecar 修复指南

## 问题分析

日志显示 `Failed to spawn Python sidecar: 系统找不到指定的文件 (os error 2)`。
这表明打包后的 EXE 中没有包含 Python sidecar 可执行文件。
这是因为 `tauri.conf.json` 中缺少了 `externalBin` 配置，Tauri 在打包时忽略了 sidecar 文件。

## 修复内容

### 1. 配置文件 `src-tauri/tauri.conf.json`

在 `bundle` 节点下添加了 `externalBin` 配置：

```json
  "bundle": {
    "active": true,
    "targets": "all",
    // ...
    "externalBin": [
      "binaries/vn-sidecar"
    ]
  }
```

这告诉 Tauri 在 `src-tauri/binaries/` 目录下查找 `vn-sidecar-<平台架构>` 文件，并将其打包。

### 2. Rust 代码 `src-tauri/src/main.rs`

更新了调用 sidecar 的代码，使其与配置文件的路径匹配：

```rust
// 修改前
let sidecar_command = shell.sidecar("vn-sidecar")

// 修改后
let sidecar_command = shell.sidecar("binaries/vn-sidecar")
```

## 下一步操作

请按以下步骤重新构建：

1.  **构建 Python Sidecar** (确保生成 `src-tauri/binaries/vn-sidecar-x86_64-pc-windows-msvc.exe`)：
    ```powershell
    cd src-python
    python build_sidecar.py --platform windows
    cd ..
    ```

2.  **重新打包 Tauri 应用**：
    ```powershell
    npm run tauri build
    ```

3.  **安装并测试**：
    运行生成的安装包或直接运行 `target/release/VideoNote.exe`。


