# VideoNote

A Mac desktop application for video note-taking built with Tauri v2 + React (Vite) + Python (FastAPI) Sidecar.

## Stage 1: Initial Setup - COMPLETED ✓

### What has been set up:

#### 1. Tauri + Vite + React + TypeScript Project ✓
- Project structure created with proper configuration
- Vite configured with `@` alias pointing to `src` directory for Shadcn compatibility
- TypeScript configured with strict mode and path mappings
- React app with a basic Hello World component

#### 2. Python FastAPI Sidecar ✓
- Created `src-python` directory with complete FastAPI application
- `requirements.txt` with all necessary dependencies:
  - fastapi
  - uvicorn
  - yt-dlp
  - pydantic
  - requests
  - pyinstaller
- Python virtual environment created and dependencies installed
- `main.py` with:
  - FastAPI server configured for random port assignment (port 0)
  - Port printed to stdout in format `SERVER_PORT=12345` for Tauri to capture
  - Health check endpoints at `/` and `/health`
  - CORS configured for Tauri frontend communication
  - Proper logging and error handling

### Project Structure:

```
videonote/
├── src/                      # React frontend source
│   ├── App.tsx              # Main React component
│   ├── main.tsx             # React entry point
│   └── styles.css           # Global styles
├── src-python/              # Python backend sidecar
│   ├── venv/                # Python virtual environment
│   ├── main.py              # FastAPI server with random port
│   └── requirements.txt     # Python dependencies
├── src-tauri/               # Tauri Rust backend
│   ├── src/
│   │   └── main.rs         # Tauri main entry
│   ├── Cargo.toml          # Rust dependencies
│   ├── build.rs            # Build script
│   └── tauri.conf.json     # Tauri configuration
├── index.html               # HTML entry point
├── vite.config.ts           # Vite config with @ alias
├── tsconfig.json            # TypeScript config
├── tsconfig.node.json       # Node TypeScript config
├── package.json             # NPM dependencies and scripts
└── README.md                # This file
```

### Next Steps:

#### Prerequisites
Before running the application, you need to install:

1. **Rust** (required for Tauri):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env
   ```

2. **Xcode Command Line Tools** (macOS):
   ```bash
   xcode-select --install
   ```

#### Running the Application

1. **Start the development server:**
   ```bash
   npm run tauri:dev
   ```

   This will:
   - Start Vite dev server on port 1420
   - Build and launch the Tauri application
   - The Python sidecar can be launched separately or integrated into Tauri

2. **Test the Python sidecar independently:**
   ```bash
   source src-python/venv/bin/activate
   python src-python/main.py
   ```

   You should see output like:
   ```
   SERVER_PORT=60710
   Starting Python Sidecar on port 60710
   INFO:     Uvicorn running on http://127.0.0.1:60710
   ```

#### Scripts Available

- `npm run dev` - Start Vite dev server only
- `npm run build` - Build the frontend for production
- `npm run tauri:dev` - Start Tauri in development mode
- `npm run tauri:build` - Build the complete application for production

### Technology Stack

- **Frontend:** React 19 + TypeScript + Vite
- **Desktop Framework:** Tauri v2
- **Backend Sidecar:** Python 3 + FastAPI + Uvicorn
- **Video Processing:** yt-dlp
- **Validation:** Pydantic

### Key Features Implemented

1. **Random Port Assignment:** The Python sidecar finds a free port automatically and communicates it to Tauri via stdout
2. **CORS Configuration:** Pre-configured to allow communication between Tauri and Python sidecar
3. **Health Check Endpoints:** `/` and `/health` endpoints for monitoring
4. **Type Safety:** Full TypeScript support with strict mode
5. **Path Aliases:** `@` alias configured for cleaner imports (ready for Shadcn)

### Verification Status

- ✅ React + Vite + TypeScript project structure
- ✅ Vite config with @ alias
- ✅ Python environment and dependencies
- ✅ FastAPI server with random port
- ✅ Python server tested and working
- ⏳ Tauri dev server (requires Rust installation)

## Stage 2: Python Backend Core Logic - COMPLETED ✓

### What has been implemented:

#### 1. Video Downloader Module (core/downloader.py) ✓
- Complete `VideoDownloader` class using yt-dlp
- Progress tracking with callback hooks
- `DownloadProgress` dataclass for structured progress updates
- Auto-detection of ffmpeg location
- Support for multiple video formats and quality preferences
- Comprehensive error handling and logging
- Convenience function `download_video()` for easy usage

**Key Features:**
- Real-time download progress (percentage, speed, ETA)
- Automatic filename handling
- Metadata extraction (title, duration, thumbnail)
- Cross-platform compatibility

#### 2. Download API Endpoints ✓
Enhanced `src-python/main.py` with:
- **POST /api/download**: Queue video downloads with background tasks
  - Accepts: `{url, save_path, format_preference}`
  - Returns: `{success, message, task_id}`
  - Background processing with FastAPI BackgroundTasks
- **GET /api/download/{task_id}**: Check download status
  - Returns progress and completion status
  - Includes file metadata when complete

**Task Management:**
- UUID-based task tracking
- Global dictionary for task status
- Progress callback factory for real-time updates
- Status tracking: queued → downloading → completed/failed

#### 3. Build and Deployment Scripts ✓

**build_sidecar.sh:**
- Automated PyInstaller build process
- Platform detection (macOS Apple Silicon/Intel, Linux)
- Correct target triple naming for Tauri
  - `vn-sidecar-aarch64-apple-darwin`
  - `vn-sidecar-x86_64-apple-darwin`
  - `vn-sidecar-x86_64-unknown-linux-gnu`
- Hidden imports configuration for uvicorn
- Collects all yt-dlp dependencies
- Outputs to `src-tauri/binaries/`
- Build verification and file size reporting

**Tauri Configuration:**
- Updated `src-tauri/tauri.conf.json` with `externalBin` configuration
- Sidecar will be bundled with the app
- Automatic platform-specific binary selection

#### 4. Testing Infrastructure ✓
- `test_api.py`: Comprehensive API test suite
  - Health check validation
  - Download endpoint testing
  - Status endpoint verification
  - Request validation testing
- `run.sh`: Quick start script for development

### Updated Project Structure:

```
videonote/
├── src-python/
│   ├── core/
│   │   ├── __init__.py
│   │   └── downloader.py       # Video downloader with yt-dlp
│   ├── venv/
│   ├── main.py                 # Enhanced with download endpoints
│   ├── requirements.txt
│   ├── build_sidecar.sh        # PyInstaller build script
│   ├── run.sh                  # Development quick start
│   ├── test_api.py             # API test suite
│   └── README.md               # Python sidecar documentation
├── src-tauri/
│   ├── binaries/               # Build output directory
│   │   └── vn-sidecar-*        # Platform-specific binaries
│   └── tauri.conf.json         # Updated with externalBin
└── ...
```

### API Documentation

#### POST /api/download
```json
{
  "url": "https://youtube.com/watch?v=...",
  "save_path": "/path/to/downloads",
  "format_preference": "best"  // optional
}
```

Response:
```json
{
  "success": true,
  "message": "Download task queued",
  "task_id": "uuid-here"
}
```

#### GET /api/download/{task_id}
Response:
```json
{
  "success": true,
  "message": "Download completed successfully",
  "task_id": "uuid-here",
  "file_path": "/path/to/video.mp4",
  "title": "Video Title",
  "duration": 180,
  "thumbnail": "https://..."
}
```

### Building the Sidecar

To build the Python sidecar binary:

```bash
cd src-python
./build_sidecar.sh
```

This will create a platform-specific binary in `src-tauri/binaries/`.

### Testing

1. Start the Python server:
   ```bash
   cd src-python
   ./run.sh
   ```

2. Run API tests (in a new terminal):
   ```bash
   cd src-python
   source venv/bin/activate
   python test_api.py 55012  # Replace with actual port
   ```

### Verification Status

- ✅ Video downloader module with yt-dlp
- ✅ Progress tracking with callbacks
- ✅ POST /api/download endpoint
- ✅ GET /api/download/{task_id} status endpoint
- ✅ Background task processing
- ✅ Build script with PyInstaller
- ✅ Tauri binary configuration
- ✅ API test suite
- ✅ Server tested and working

## Stage 3: Tauri Bridge Configuration - COMPLETED ✓

### What has been implemented:

#### 1. Tauri Configuration ✓
Updated `src-tauri/tauri.conf.json` with:
- `externalBin` configuration for Python sidecar
- Shell plugin scope for vn-sidecar
- Global Tauri access enabled

#### 2. Rust Sidecar Launch Logic ✓
Implemented in `src-tauri/src/main.rs`:
- `SidecarState` struct to store Python port
- `get_sidecar_port` Tauri command for frontend
- Async sidecar spawning with `shell.sidecar()`
- Stdout monitoring to extract `SERVER_PORT=xxxxx`
- Port storage in Rust state
- Event emission to frontend (`sidecar-port` event)
- Error handling with development fallback

**Key Features:**
- Automatic port extraction via regex
- Both event-based and invoke-based port access
- Graceful error handling
- Development mode support (manual Python server)

#### 3. Rust Dependencies ✓
Added to `Cargo.toml`:
- `tauri-plugin-dialog` for folder selection

## Stage 4: Frontend UI Development - COMPLETED ✓

### What has been implemented:

#### 1. Shadcn/UI Setup ✓
- Installed Tailwind CSS, PostCSS, Autoprefixer
- Configured `tailwind.config.js` with Shadcn theme
- Set up CSS variables for light/dark mode
- Created utility functions (`cn()` for class merging)

**Components Created:**
- `Button` component with variants (default, destructive, outline, etc.)
- `Input` component with proper styling
- `Card` components (Card, CardHeader, CardTitle, CardDescription, CardContent)
- `Progress` component for download progress

#### 2. API Client (lib/api.ts) ✓
Complete API client with:
- Port discovery via Tauri events and invoke
- Automatic retry and polling mechanism
- Base URL construction with dynamic port
- Type-safe methods:
  - `healthCheck()` - Check Python backend status
  - `startDownload(url, savePath)` - Initiate download
  - `getDownloadStatus(taskId)` - Poll download progress

**Features:**
- Promise-based port initialization
- Event listener for sidecar-port
- Polling fallback if event missed
- 30-second timeout with clear error messages
- Singleton pattern for app-wide use

#### 3. Download Page UI ✓
Complete download interface (`components/DownloadPage.tsx`):

**Features:**
- URL input with validation
- Folder picker using Tauri dialog plugin
- Download button with loading state
- Real-time progress tracking (polling every 2 seconds)
- Success/error message display
- Download status visualization
- Reset functionality

**UI States:**
- Idle (ready for new download)
- Downloading (shows progress bar and spinner)
- Completed (success message with file path)
- Failed (error message with details)

**Visual Feedback:**
- API connection status indicator
- Animated loader during download
- Progress bar with percentage
- Success/error icons and colored alerts
- File path display on completion

### Project Structure Updates:

```
src/
├── components/
│   ├── ui/
│   │   ├── button.tsx           # Button component
│   │   ├── input.tsx            # Input component
│   │   ├── card.tsx             # Card components
│   │   └── progress.tsx         # Progress bar
│   └── DownloadPage.tsx         # Main download UI
├── lib/
│   ├── utils.ts                 # Utility functions (cn)
│   └── api.ts                   # API client singleton
├── App.tsx                      # Updated to use DownloadPage
├── main.tsx                     # React entry point
└── styles.css                   # Tailwind + Shadcn styles

Configuration:
├── tailwind.config.js           # Tailwind configuration
├── postcss.config.js            # PostCSS configuration
└── tsconfig.json                # TypeScript configuration

src-tauri/
├── src/
│   └── main.rs                  # Updated with sidecar + dialog
├── Cargo.toml                   # Added dialog plugin
└── tauri.conf.json              # Updated with plugins
```

### Dependencies Added:

**Frontend:**
- `tailwindcss` - Utility-first CSS framework
- `postcss` & `autoprefixer` - CSS processing
- `class-variance-authority` - Component variants
- `clsx` & `tailwind-merge` - Class name utilities
- `lucide-react` - Icon library
- `@tauri-apps/plugin-dialog` - File/folder picker

**Rust:**
- `tauri-plugin-dialog` - Dialog functionality

### Verification Status:

- ✅ Tauri sidecar configuration
- ✅ Python port extraction from stdout
- ✅ Rust state management
- ✅ Event emission to frontend
- ✅ Tailwind CSS + Shadcn setup
- ✅ UI components library
- ✅ API client with dynamic port
- ✅ Download page with all features
- ✅ Folder picker integration
- ✅ Progress tracking
- ✅ Error handling

## Running the Application

### Development Mode:

**方式一: 一体化启动(推荐)**
```bash
npm run tauri:dev
```
这会自动启动Python sidecar(使用动态端口)和前端。

**方式二: 分离启动(用于调试)**

1. **手动启动Python backend:**
   ```bash
   cd src-python
   ./run.sh
   # 或指定端口: python main.py --port 8000
   ```

2. **启动Tauri dev server:**
   ```bash
   npm run tauri:dev
   ```

**方式三: 仅前端开发**
```bash
npm run dev
```

### 端口配置

- **动态端口(默认)**: Python sidecar自动选择可用端口
- **固定端口(可选)**: 使用 `--port` 参数指定端口
- **查看当前端口**: 查看应用日志中的 `Extracted sidecar port` 行

### Using the App:

1. 等待应用启动并显示"就绪"状态(通常10-30秒)
2. 输入视频URL (例如: YouTube链接)
3. 点击文件夹图标选择下载位置
4. 点击"开始下载"按钮
5. 查看进度条和状态更新
6. 下载完成后会显示文件路径

### 技术特性

- **动态端口分配**: Python sidecar自动选择可用端口,避免端口冲突
- **多实例支持**: 可以同时运行多个VideoNote实例
- **自动重连**: 前端会自动重试连接后端
- **智能日志**: 只有真正的错误才会标记为ERROR级别

## Windows Deployment - FIXED ✓

### Issues Fixed (2025-12-08):

#### 1. ✅ Misleading ERROR Logs
**Problem**: All stderr outputs were marked as ERROR level, causing users to think the app was failing
**Fix**: Modified `src-tauri/src/main.rs` to only mark actual errors (containing keywords like "error", "failed", "exception") as ERROR level

#### 2. ✅ CSP (Content Security Policy) Restrictions
**Problem**: Windows builds might fail to connect to localhost:8118 Python backend due to CSP
**Fix**: Added proper CSP configuration in `src-tauri/tauri.conf.json` explicitly allowing connections to 127.0.0.1:8118

### Windows Build Instructions:

**NEW**: ffmpeg 现在会自动下载和打包! 🎉

1. **Build Python Sidecar (自动下载 ffmpeg):**
   ```bash
   cd src-python
   # Windows 构建 (在任何平台上)
   python build_sidecar.py --platform windows
   
   # 或当前平台构建
   python build_sidecar.py
   ```

2. **Build Tauri App:**
   ```bash
   npm run tauri:build
   ```

3. **Find Installer:**
   The installer will be in `src-tauri/target/release/bundle/`

**详细构建指南**: [WINDOWS_BUILD_GUIDE.md](WINDOWS_BUILD_GUIDE.md)

**注意**: PyInstaller 有跨平台限制，要生成 Windows .exe 最好在 Windows 上构建。推荐使用 GitHub Actions 进行多平台构建。

### Troubleshooting on Windows:

See detailed troubleshooting guide: [WINDOWS_DEPLOYMENT.md](WINDOWS_DEPLOYMENT.md)

**Quick Diagnostic Tool:**
```powershell
.\troubleshoot.ps1
```

This script will:
- Check system information
- Verify port 8118 availability
- Check firewall rules
- Verify app installation
- Analyze log files
- Test network connectivity
- Detect security software

### Common Windows Issues:

1. **Windows Firewall**: Allow the app when prompted
2. **Antivirus Software**: Add VideoNote to whitelist
3. **Port Conflicts**: Port 8118 might be occupied
4. **First Launch**: May take 10-30 seconds to initialize

### Log Location:

- **Runtime Logs**: `%APPDATA%\VideoNote\logs\`
- **In-App Viewer**: Click log icon in top-right corner

## Cross-Platform Status

- ✅ **macOS** (Apple Silicon & Intel): Fully tested
- ✅ **Windows** (Windows 10/11): Fixed and tested
- ⏳ **Linux**: Should work but not extensively tested

## Next Steps

- Add video player integration
- Implement note-taking features
- Add video library/history
- Support for batch downloads
- WebSocket for real-time progress (instead of polling)
- Thumbnail preview
- Duration and metadata display
- Settings page for format preferences
