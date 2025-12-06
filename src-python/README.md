# VideoNote Python Sidecar

Python backend service for VideoNote application. Handles video downloading using yt-dlp.

## Features

- FastAPI-based REST API
- Video downloading with yt-dlp
- Progress tracking for downloads
- Background task processing
- Automatic port assignment for Tauri integration
- Cross-platform support (macOS, Linux)

## Project Structure

```
src-python/
├── core/
│   ├── __init__.py
│   └── downloader.py        # Video downloader module with yt-dlp
├── venv/                    # Python virtual environment
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── build_sidecar.sh        # Build script for PyInstaller
├── run.sh                  # Quick start script
├── test_api.py             # API test script
└── README.md               # This file
```

## API Endpoints

### Health Check

**GET /** or **GET /health**
- Returns server status
- Response: `{"status": "ok", "message": "Python Sidecar is running"}`

### Download Video

**POST /api/download**

Request body:
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "save_path": "/path/to/save/directory",
  "format_preference": "best"  // optional, default: "best"
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

### Check Download Status

**GET /api/download/{task_id}**

Response (in progress):
```json
{
  "success": true,
  "message": "Download status: downloading",
  "task_id": "uuid-here"
}
```

Response (completed):
```json
{
  "success": true,
  "message": "Download completed successfully",
  "task_id": "uuid-here",
  "file_path": "/path/to/downloaded/video.mp4",
  "title": "Video Title",
  "duration": 180,
  "thumbnail": "https://..."
}
```

## Development

### Prerequisites

- Python 3.8 or higher
- ffmpeg (optional but recommended)
  ```bash
  # macOS
  brew install ffmpeg

  # Linux
  sudo apt-get install ffmpeg
  ```

### Setup

1. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Server

**Quick start:**
```bash
./run.sh
```

**Manual start:**
```bash
source venv/bin/activate
python main.py
```

The server will:
1. Find a free port automatically
2. Print `SERVER_PORT=12345` to stdout (for Tauri to capture)
3. Start the FastAPI server on that port

### Testing

Run the API test suite:
```bash
# Start the server first
./run.sh &
SERVER_PID=$!

# Wait for server to start and capture the port
sleep 2
PORT=$(jobs -p $SERVER_PID | xargs ps -o command= -p | grep -oE 'SERVER_PORT=([0-9]+)' | cut -d= -f2)

# Run tests
source venv/bin/activate
python test_api.py $PORT

# Stop the server
kill $SERVER_PID
```

## Building for Production

### Build the Sidecar Binary

The build script uses PyInstaller to create a standalone executable:

```bash
./build_sidecar.sh
```

This will:
1. Activate the virtual environment
2. Clean previous builds
3. Run PyInstaller with optimized settings
4. Output binary to `../src-tauri/binaries/`
5. Name it according to target platform:
   - `vn-sidecar-aarch64-apple-darwin` (Apple Silicon)
   - `vn-sidecar-x86_64-apple-darwin` (Intel Mac)
   - `vn-sidecar-x86_64-unknown-linux-gnu` (Linux)

### PyInstaller Configuration

The build script includes:
- Single-file executable (`--onefile`)
- Hidden imports for uvicorn
- Collected yt-dlp data files
- Automatic target triple detection

### Integrating with Tauri

The sidecar binary is configured in `src-tauri/tauri.conf.json`:

```json
{
  "bundle": {
    "externalBin": [
      "binaries/vn-sidecar"
    ]
  }
}
```

Tauri will automatically:
1. Include the correct platform binary in the app bundle
2. Launch the sidecar when the app starts
3. Manage the sidecar process lifecycle

## Core Modules

### downloader.py

Handles video downloading with yt-dlp.

**Key Classes:**
- `DownloadProgress`: Progress information dataclass
- `VideoDownloader`: Main downloader class with progress tracking

**Key Functions:**
- `download_video(url, save_path, progress_callback, ffmpeg_location)`: Download a video

**Features:**
- Progress hooks for real-time updates
- ffmpeg integration for format conversion
- Automatic format selection
- Error handling and logging

### main.py

FastAPI application with:
- Background task processing
- Download task tracking
- Progress monitoring
- CORS configuration for Tauri

## Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **yt-dlp**: Video downloader
- **pydantic**: Data validation
- **requests**: HTTP client
- **pyinstaller**: Executable bundler

## Platform Support

- macOS (Apple Silicon and Intel)
- Linux (x86_64)
- Windows support can be added by updating the build script

## Troubleshooting

### ffmpeg not found

Install ffmpeg for your platform:
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### Build fails

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Clean build artifacts:
   ```bash
   rm -rf build dist *.spec
   ```

3. Try building again:
   ```bash
   ./build_sidecar.sh
   ```

### Port already in use

The server automatically finds a free port, but if you need a specific port, modify `main.py`:

```python
# Instead of:
port = find_free_port()

# Use:
port = 8000  # Your preferred port
```

## License

Part of the VideoNote project.
