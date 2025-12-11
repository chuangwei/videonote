# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VideoNote is a cross-platform desktop application for video note-taking built with:
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS + Shadcn/UI
- **Desktop Framework**: Tauri v2 (Rust)
- **Backend Sidecar**: Python 3 + FastAPI + Uvicorn
- **Video Processing**: yt-dlp with ffmpeg

## Essential Commands

### Development
```bash
npm run tauri:dev          # Start Tauri app with Python sidecar (recommended)
npm run dev                # Start Vite dev server only
cd src-python && ./run.sh  # Manually start Python sidecar for debugging
```

### Building
```bash
# Build Python sidecar with automatic ffmpeg download
cd src-python
python build_sidecar.py              # Current platform
python build_sidecar.py --platform windows  # Cross-platform build

# Build Tauri application
npm run tauri:build        # Creates installer in src-tauri/target/release/bundle/
```

### Testing
```bash
npm run build              # Build frontend only
cd src-python && source venv/bin/activate && python test_api.py [port]  # Test Python API
```

## Architecture Overview

### Three-Layer Architecture

1. **Frontend (React/TypeScript)**: User interface in `src/`
   - Entry: `src/main.tsx` → `src/App.tsx`
   - Main UI: `src/components/DownloadPage.tsx`
   - API Client: `src/lib/api.ts` (singleton)
   - Shadcn components: `src/components/ui/`

2. **Tauri Layer (Rust)**: Desktop wrapper in `src-tauri/src/main.rs`
   - Spawns Python sidecar process via `shell.sidecar()`
   - Monitors stdout for `SERVER_PORT=XXXXX` to extract dynamic port
   - Emits `sidecar-port` event to frontend
   - Provides `get_sidecar_port` command for frontend queries
   - Manages plugins: dialog, fs, log, shell

3. **Python Sidecar (FastAPI)**: Backend service in `src-python/`
   - Entry: `main.py` (FastAPI app with dynamic port assignment)
   - Core logic: `core/downloader.py` (VideoDownloader class using yt-dlp)
   - Build: `build_sidecar.py` (PyInstaller bundling with ffmpeg)
   - Packaged as single binary: `src-tauri/binaries/vn-sidecar-{target-triple}`

### Dynamic Port Communication Flow

This is **critical** to understand:

1. Python sidecar starts with `--port 0` (auto-assign free port)
2. `main.py:find_free_port()` finds available port
3. After server initialization, prints `SERVER_PORT=12345` to **stdout**
4. Rust monitors sidecar stdout, extracts port via regex
5. Rust stores port in `SidecarState` and emits `sidecar-port` event
6. Frontend (`api.ts`) listens for event or polls via `get_sidecar_port`
7. Frontend constructs API URLs: `http://127.0.0.1:{dynamic-port}`

**Important**: Port announcement happens on stdout ONLY. Stderr is for logs. Do not mix them.

### API Endpoints

- `GET /health` - Health check
- `POST /api/download` - Queue video download, returns `task_id`
  - Request: `{url, save_path, format_preference?}`
- `GET /api/download/{task_id}` - Poll download status/progress

### FFmpeg Handling

- `download_ffmpeg.py`: Auto-downloads platform-specific ffmpeg binaries
  - Windows: Downloads from GitHub releases (~100 MB)
  - macOS: Uses Homebrew-installed ffmpeg
  - Cached in `src-python/.ffmpeg_cache/{platform}/`
- `build_sidecar.py`: Bundles ffmpeg into PyInstaller binary via `--add-binary`
  - Verifies ffmpeg file size (should be ~100 MB for Windows)
  - Final sidecar should be ~150 MB on Windows (includes Python + yt-dlp + ffmpeg)
- `core/downloader.py`: Auto-detects ffmpeg from PyInstaller bundle (`sys._MEIPASS`) or system PATH
  - **Fallback strategy**: If ffmpeg not found, downloads pre-merged formats only (lower quality but won't fail)
  - Detailed logging with `[ffmpeg]` prefix for debugging
- Windows builds require ffmpeg.exe bundled due to lack of system ffmpeg
- **IMPORTANT**: PyInstaller does NOT support cross-compilation - Windows sidecar must be built on Windows

## Key Development Patterns

### Path Aliases
- `@/` maps to `src/` (configured in `vite.config.ts` and `tsconfig.json`)
- Use `import { Button } from "@/components/ui/button"` instead of relative paths

### Shadcn/UI Components
- Components are copied into `src/components/ui/` (not installed via npm)
- Tailwind CSS v4 with CSS variables for theming in `src/styles.css`
- Use `cn()` utility from `@/lib/utils` for conditional class names

### Python Virtual Environment
- Located at `src-python/venv/`
- Activate: `source src-python/venv/bin/activate`
- Dependencies: `src-python/requirements.txt`

### Tauri Configuration
- Main config: `src-tauri/tauri.conf.json`
- **CSP**: Allows connections to `http://127.0.0.1:*` and `http://localhost:*`
- **externalBin**: `binaries/vn-sidecar` (auto-suffixed with target triple by Tauri)
- **Shell plugin scope**: Configured for sidecar execution

### Cross-Platform Considerations

**macOS**:
- Native ffmpeg via brew or bundled
- Target triples: `aarch64-apple-darwin` (Apple Silicon), `x86_64-apple-darwin` (Intel)

**Windows**:
- Must bundle ffmpeg.exe (no system PATH)
- Use `python build_sidecar.py --platform windows` for cross-compilation prep
- PyInstaller cross-platform limitations: best to build on Windows for Windows
- Stdout buffering issues handled in `main.py` lines 14-22

**Linux**:
- Target triple: `x86_64-unknown-linux-gnu`
- Less tested than macOS/Windows

## Important Implementation Details

### Stderr vs Stdout in Python Sidecar
- **Stdout**: Reserved for `SERVER_PORT=XXXXX` announcement ONLY
- **Stderr**: All logging (`print(file=sys.stderr)`)
- Rust filters stderr logs: only marks as ERROR if contains "error", "failed", or "exception"
- This prevents normal logs from appearing as errors in Tauri console

### Video Format Preference
- Default format: `"bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best"`
- Forces mp4/h264 output for QuickTime compatibility
- Configured in `core/downloader.py:166`

### Progress Tracking
- Frontend polls `/api/download/{task_id}` every 2 seconds during download
- Python uses yt-dlp progress hooks to update `download_tasks` dictionary
- Progress includes: status, percent, speed, eta, filename

### Build Process
1. `build_sidecar.py` downloads/finds ffmpeg
2. PyInstaller bundles: main.py + core/ + yt-dlp + ffmpeg + uvicorn
3. Output: Single executable in `src-tauri/binaries/vn-sidecar-{triple}`
4. Tauri build packages sidecar + frontend into installer

## Common Gotchas

1. **Port not available**: Frontend shows "API connection status" indicator. Wait 10-30s for sidecar initialization.

2. **PyInstaller hidden imports**: Uvicorn requires explicit `--hidden-import` flags (see `build_sidecar.py:126-135`)

3. **yt-dlp updates**: Use `--collect-all=yt_dlp` to bundle all dependencies

4. **Path aliases**: Ensure Vite `resolve.alias` and `tsconfig.json` paths match for `@/` imports

5. **Windows buffering**: `main.py` lines 14-22 fix encoding/buffering for Windows stdout

6. **Sidecar termination**: Tauri auto-kills sidecar on app exit

7. **CSP violations**: If API calls fail, check `tauri.conf.json` CSP `connect-src` includes the port range

8. **ffmpeg not found on Windows**:
   - Error: "You have requested merging of multiple formats but ffmpeg is not installed"
   - Solution: Rebuild sidecar on Windows: `cd src-python && python build_sidecar.py`
   - Verify: Check sidecar size is ~150 MB (not ~50 MB)
   - Logs should show: `[ffmpeg] ✓ Found bundled ffmpeg.exe`

9. **Cross-compilation doesn't work**: PyInstaller cannot cross-compile. Windows binaries must be built on Windows, macOS on macOS, etc. Use GitHub Actions for multi-platform builds.

## File Structure (Key Locations)

```
videonote/
├── src/                          # React frontend
│   ├── components/
│   │   ├── DownloadPage.tsx      # Main UI component
│   │   └── ui/                   # Shadcn components
│   ├── lib/
│   │   └── api.ts                # API client singleton
│   └── App.tsx                   # Root component
├── src-tauri/                    # Tauri (Rust)
│   ├── src/main.rs               # Sidecar spawning logic
│   ├── tauri.conf.json           # Tauri configuration
│   └── binaries/                 # Python sidecar binaries
├── src-python/                   # Python backend
│   ├── main.py                   # FastAPI server
│   ├── core/downloader.py        # Video download logic
│   ├── build_sidecar.py          # Build script
│   └── download_ffmpeg.py        # FFmpeg auto-download
└── package.json                  # NPM scripts
```

## Development Workflow

1. **Starting development**: `npm run tauri:dev` launches everything
2. **Python changes**: Restart Tauri app (sidecar is bundled in dev mode via `shell.sidecar`)
3. **Frontend changes**: Vite hot-reload handles automatically
4. **Rust changes**: Tauri auto-rebuilds
5. **Debugging Python**: Run sidecar manually with `./src-python/run.sh` and check stderr output
6. **Debugging Tauri**: DevTools via Cmd+Shift+I (macOS) or Ctrl+Shift+I (Windows)

## Testing

The application has been tested on:
- macOS (Apple Silicon & Intel) ✅
- Windows 10/11 ✅
- Linux (limited testing) ⚠️
