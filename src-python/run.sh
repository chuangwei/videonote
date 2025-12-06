#!/bin/bash
# Quick start script for Python sidecar

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run the FastAPI server
python "$SCRIPT_DIR/main.py"
