# Windows Build Verification Script
# This script verifies that ffmpeg is properly bundled in the Windows sidecar

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Windows Sidecar Build Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if sidecar binary exists
$sidecarPath = "src-tauri\binaries\vn-sidecar-x86_64-pc-windows-msvc.exe"

if (-not (Test-Path $sidecarPath)) {
    Write-Host "ERROR: Sidecar binary not found at: $sidecarPath" -ForegroundColor Red
    Write-Host "Run: cd src-python && python build_sidecar.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "OK: Sidecar binary found" -ForegroundColor Green

# Check file size
$sidecarSize = (Get-Item $sidecarPath).Length / 1MB
Write-Host "Sidecar size: $([math]::Round($sidecarSize, 2)) MB" -ForegroundColor Cyan

# Verify size is reasonable (should be ~150 MB with ffmpeg)
if ($sidecarSize -lt 100) {
    Write-Host "WARNING: Sidecar is too small ($([math]::Round($sidecarSize, 2)) MB)" -ForegroundColor Red
    Write-Host "Expected: ~150 MB (with ffmpeg bundled)" -ForegroundColor Yellow
    Write-Host "Actual: $([math]::Round($sidecarSize, 2)) MB" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This indicates ffmpeg was NOT properly bundled!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Check if ffmpeg was downloaded:" -ForegroundColor White
    Write-Host "   src-python\.ffmpeg_cache\windows\ffmpeg.exe" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Manually download ffmpeg:" -ForegroundColor White
    Write-Host "   cd src-python" -ForegroundColor Gray
    Write-Host "   python download_ffmpeg.py --platform windows" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Rebuild sidecar:" -ForegroundColor White
    Write-Host "   cd src-python" -ForegroundColor Gray
    Write-Host "   python build_sidecar.py" -ForegroundColor Gray
    Write-Host ""
    exit 1
} else {
    Write-Host "OK: Sidecar size looks good (ffmpeg appears to be bundled)" -ForegroundColor Green
}

# Check if ffmpeg cache exists
$ffmpegCachePath = "src-python\.ffmpeg_cache\windows\ffmpeg.exe"
if (Test-Path $ffmpegCachePath) {
    $ffmpegSize = (Get-Item $ffmpegCachePath).Length / 1MB
    Write-Host "OK: ffmpeg found in cache ($([math]::Round($ffmpegSize, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "WARNING: ffmpeg not found in cache" -ForegroundColor Yellow
    Write-Host "Path: $ffmpegCachePath" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sidecar path: $sidecarPath" -ForegroundColor White
Write-Host "Sidecar size: $([math]::Round($sidecarSize, 2)) MB" -ForegroundColor White
Write-Host "Status: " -NoNewline -ForegroundColor White
if ($sidecarSize -ge 100) {
    Write-Host "PASS" -ForegroundColor Green
} else {
    Write-Host "FAIL" -ForegroundColor Red
}
Write-Host ""

Write-Host "To test the sidecar, run it directly:" -ForegroundColor Cyan
Write-Host "  .\$sidecarPath" -ForegroundColor Gray
Write-Host ""
Write-Host "Look for this line in the output:" -ForegroundColor Cyan
Write-Host "  [ffmpeg] OK Found bundled ffmpeg.exe" -ForegroundColor Gray
Write-Host ""
