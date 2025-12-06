#!/bin/bash
# Quick integration test for VideoNote Python Sidecar

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "================================================"
echo "VideoNote Python Sidecar - Quick Test"
echo "================================================"
echo ""

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Start the server in background
echo "Starting Python sidecar..."
python "$SCRIPT_DIR/main.py" > /tmp/videonote_server.log 2>&1 &
SERVER_PID=$!

echo "Server PID: $SERVER_PID"

# Wait for server to start and extract port
sleep 2

# Read the port from the log
PORT=$(grep -oE 'SERVER_PORT=[0-9]+' /tmp/videonote_server.log | head -1 | cut -d= -f2)

if [ -z "$PORT" ]; then
    echo "Error: Failed to detect server port"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo "Server running on port: $PORT"
echo ""

# Run tests
echo "Running API tests..."
echo "================================================"
python "$SCRIPT_DIR/test_api.py" $PORT
TEST_RESULT=$?

echo ""
echo "================================================"

# Cleanup
echo "Stopping server..."
kill $SERVER_PID 2>/dev/null || true
sleep 1

# Remove log file
rm -f /tmp/videonote_server.log

if [ $TEST_RESULT -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Tests failed!"
    exit 1
fi
