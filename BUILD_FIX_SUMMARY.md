# GitHub Actions 构建修复总结

## 问题诊断

GitHub Actions 在 Windows 和 macOS 平台上构建失败，错误信息：
```
Error `tauri.conf.json` error on `app > windows > 0`: Additional properties are not allowed ('devTools' was unexpected)
Error: Command "npm ["run","tauri","build"]" failed with exit code 1
```

## 根本原因

Tauri 2.0 对配置文件进行了重大更改：
1. `devTools` 属性不再被允许在 `tauri.conf.json` 的窗口配置中
2. Sidecar 配置方式从 `externalBin` 数组改为在 `build.rs` 中声明

## 修复内容

### 1. 修改 `src-tauri/tauri.conf.json`

**删除了不支持的属性：**
- 从窗口配置中删除 `devTools: true` 属性
- 删除 `bundle.externalBin` 配置（移至 build.rs）

修改前：
```json
"windows": [
  {
    "title": "VideoNote",
    "width": 1200,
    "height": 800,
    "resizable": true,
    "fullscreen": false,
    "devTools": true  // ❌ 不再支持
  }
]
```

修改后：
```json
"windows": [
  {
    "title": "VideoNote",
    "width": 1200,
    "height": 800,
    "resizable": true,
    "fullscreen": false
  }
]
```

### 2. 修改 `src-tauri/build.rs`

**添加 Sidecar 配置：**

修改前：
```rust
fn main() {
    tauri_build::build()
}
```

修改后：
```rust
fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .sidecar("vn-sidecar"),
    )
    .expect("failed to build");
}
```

这告诉 Tauri 构建系统查找名为 `vn-sidecar` 的二进制文件，并根据目标平台自动添加正确的后缀：
- Windows: `vn-sidecar-x86_64-pc-windows-msvc.exe`
- macOS (Intel): `vn-sidecar-x86_64-apple-darwin`
- macOS (ARM): `vn-sidecar-aarch64-apple-darwin`

## 验证

修复后的构建流程：
1. ✅ Python sidecar 通过 `build_sidecar.py` 构建
2. ✅ 二进制文件放置在 `src-tauri/binaries/` 目录
3. ✅ Tauri 构建系统通过 `build.rs` 识别 sidecar
4. ✅ 配置文件符合 Tauri 2.0 规范

## 注意事项

- DevTools 功能仍然可以通过代码中的 `window.open_devtools()` 方法使用
- Sidecar 在开发和生产环境中都能正常工作
- GitHub Actions 工作流无需修改，Python sidecar 构建步骤已正确配置

## 相关文件

- `src-tauri/tauri.conf.json` - 主配置文件
- `src-tauri/build.rs` - 构建脚本
- `src-tauri/src/main.rs` - 包含 sidecar 启动逻辑
- `src-python/build_sidecar.py` - Python sidecar 构建脚本
- `.github/workflows/release.yml` - CI/CD 工作流

