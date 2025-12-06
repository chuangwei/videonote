#!/bin/bash
# Build script for VideoNote Python Sidecar
# Uses PyInstaller to create a standalone executable

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_ROOT/src-tauri/binaries"

echo "================================================"
echo "Building VideoNote Python Sidecar"
echo "================================================"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

# Ensure PyInstaller is installed
echo "Checking PyInstaller installation..."
pip show pyinstaller > /dev/null 2>&1 || {
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
}

# Detect platform and architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Detected OS: $OS"
echo "Detected Architecture: $ARCH"

# Determine the binary name based on platform
# Tauri expects format: <binary-name>-<target-triple>
# Examples:
#   - vn-sidecar-aarch64-apple-darwin (Apple Silicon Mac)
#   - vn-sidecar-x86_64-apple-darwin (Intel Mac)
#   - vn-sidecar-x86_64-unknown-linux-gnu (Linux)

if [[ "$OS" == "Darwin" ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
        TARGET="aarch64-apple-darwin"
    else
        TARGET="x86_64-apple-darwin"
    fi
elif [[ "$OS" == "Linux" ]]; then
    TARGET="x86_64-unknown-linux-gnu"
else
    echo "Unsupported platform: $OS"
    exit 1
fi

BINARY_NAME="vn-sidecar-$TARGET"

echo "Target binary name: $BINARY_NAME"
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "Building with PyInstaller..."
echo ""

# Build with PyInstaller
# Options:
#   --onefile: Create a single executable file
#   --name: Name of the executable
#   --clean: Clean PyInstaller cache before building
#   --noconfirm: Replace output directory without asking
#   --add-data: Include additional data files (if needed)
#   --hidden-import: Force import of modules that PyInstaller might miss

cd "$SCRIPT_DIR"

pyinstaller \
    --onefile \
    --name "$BINARY_NAME" \
    --clean \
    --noconfirm \
    --hidden-import=uvicorn.logging \
    --hidden-import=uvicorn.loops \
    --hidden-import=uvicorn.loops.auto \
    --hidden-import=uvicorn.protocols \
    --hidden-import=uvicorn.protocols.http \
    --hidden-import=uvicorn.protocols.http.auto \
    --hidden-import=uvicorn.protocols.websockets \
    --hidden-import=uvicorn.protocols.websockets.auto \
    --hidden-import=uvicorn.lifespan \
    --hidden-import=uvicorn.lifespan.on \
    --collect-all=yt_dlp \
    main.py

echo ""
echo "Build complete!"
echo ""

# Copy to Tauri binaries directory
echo "Copying binary to Tauri binaries directory..."
cp "$SCRIPT_DIR/dist/$BINARY_NAME" "$OUTPUT_DIR/"

# Make it executable
chmod +x "$OUTPUT_DIR/$BINARY_NAME"

echo "Binary copied to: $OUTPUT_DIR/$BINARY_NAME"
echo ""

# Display file size
FILE_SIZE=$(du -h "$OUTPUT_DIR/$BINARY_NAME" | cut -f1)
echo "Binary size: $FILE_SIZE"
echo ""

# Test the binary
echo "Testing the binary..."
"$OUTPUT_DIR/$BINARY_NAME" --help > /dev/null 2>&1 && {
    echo "✓ Binary is executable"
} || {
    echo "✗ Warning: Binary test failed"
}

echo ""
echo "================================================"
echo "Build completed successfully!"
echo "================================================"
echo ""
echo "Binary location: $OUTPUT_DIR/$BINARY_NAME"
echo ""
echo "Next steps:"
echo "1. Update src-tauri/tauri.conf.json to reference this binary"
echo "2. Run 'npm run tauri:build' to create the final app bundle"
