# Windows Build Verification Script
# Purpose: Automate the verification of VideoNote Windows build process
# Usage: .\test_windows_build.ps1

param(
    [switch]$FullBuild = $false,
    [switch]$QuickCheck = $false
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  VideoNote Windows Build Verification Tool" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Color helper functions
function Write-Success($message) {
    Write-Host "✓ $message" -ForegroundColor Green
}

function Write-Failure($message) {
    Write-Host "✗ $message" -ForegroundColor Red
}

function Write-Warning-Custom($message) {
    Write-Host "⚠ $message" -ForegroundColor Yellow
}

function Write-Info($message) {
    Write-Host "→ $message" -ForegroundColor Cyan
}

# Step 0: Environment Check
Write-Host "`n[Step 0] Checking Environment..." -ForegroundColor Yellow
Write-Host "----------------------------------------"

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Failure "Python not found! Please install Python 3.10+"
    exit 1
}

# Check if in correct directory
if (-not (Test-Path "src-python/build_sidecar.py")) {
    Write-Failure "Not in project root directory!"
    Write-Info "Please run this script from the videonote project root"
    exit 1
}
Write-Success "In correct directory"

# Check PyInstaller
try {
    $pyinstallerVersion = python -m pip show pyinstaller 2>&1 | Select-String "Version:"
    Write-Success "PyInstaller found: $pyinstallerVersion"
} catch {
    Write-Warning-Custom "PyInstaller may not be installed"
    Write-Info "Run: pip install -r src-python/requirements.txt"
}

# Step 1: Check ffmpeg Download
Write-Host "`n[Step 1] Verifying ffmpeg Download..." -ForegroundColor Yellow
Write-Host "----------------------------------------"

$ffmpegPath = "src-python/.ffmpeg_cache/windows/ffmpeg.exe"
$ffmpegOK = $false

if (Test-Path $ffmpegPath) {
    $ffmpegSize = (Get-Item $ffmpegPath).Length
    $ffmpegMB = [math]::Round($ffmpegSize / 1MB, 2)

    if ($ffmpegSize -gt 50MB) {
        Write-Success "ffmpeg.exe exists: $ffmpegMB MB"
        $ffmpegOK = $true
    } else {
        Write-Failure "ffmpeg.exe too small: $ffmpegMB MB (expected >50 MB)"
        Write-Info "Attempting to download ffmpeg..."

        Push-Location src-python
        try {
            python download_ffmpeg.py --platform windows
            Pop-Location

            if (Test-Path $ffmpegPath) {
                $ffmpegSize = (Get-Item $ffmpegPath).Length
                $ffmpegMB = [math]::Round($ffmpegSize / 1MB, 2)
                if ($ffmpegSize -gt 50MB) {
                    Write-Success "ffmpeg downloaded successfully: $ffmpegMB MB"
                    $ffmpegOK = $true
                }
            }
        } catch {
            Pop-Location
            Write-Failure "ffmpeg download failed: $_"
        }
    }
} else {
    Write-Failure "ffmpeg.exe not found"
    Write-Info "Attempting to download..."

    Push-Location src-python
    try {
        python download_ffmpeg.py --platform windows
        Pop-Location

        if (Test-Path $ffmpegPath) {
            $ffmpegSize = (Get-Item $ffmpegPath).Length
            $ffmpegMB = [math]::Round($ffmpegSize / 1MB, 2)
            if ($ffmpegSize -gt 50MB) {
                Write-Success "ffmpeg downloaded: $ffmpegMB MB"
                $ffmpegOK = $true
            } else {
                Write-Failure "Downloaded ffmpeg is too small"
            }
        }
    } catch {
        Pop-Location
        Write-Failure "Failed to download ffmpeg: $_"
    }
}

if (-not $ffmpegOK) {
    Write-Failure "Cannot proceed without valid ffmpeg"
    Write-Info "Manual download: https://github.com/GyanD/codexffmpeg/releases/download/7.0.2/ffmpeg-7.0.2-essentials_build.zip"
    exit 1
}

# Quick check mode - exit here
if ($QuickCheck) {
    Write-Host "`n[Quick Check Complete]" -ForegroundColor Green
    exit 0
}

# Step 2: Build Python Sidecar
if ($FullBuild) {
    Write-Host "`n[Step 2] Building Python Sidecar..." -ForegroundColor Yellow
    Write-Host "----------------------------------------"

    Push-Location src-python
    try {
        Write-Info "Starting build process..."
        python build_sidecar.py

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Build script completed"
        } else {
            Write-Failure "Build script failed with exit code $LASTEXITCODE"
            Pop-Location
            exit 1
        }
    } catch {
        Write-Failure "Build failed: $_"
        Pop-Location
        exit 1
    }
    Pop-Location
} else {
    Write-Host "`n[Step 2] Skipping build (use -FullBuild to build)" -ForegroundColor Yellow
}

# Step 3: Verify .spec file
Write-Host "`n[Step 3] Checking PyInstaller .spec file..." -ForegroundColor Yellow
Write-Host "----------------------------------------"

$specFile = "src-python/vn-sidecar-x86_64-pc-windows-msvc.exe.spec"
if (Test-Path $specFile) {
    $specContent = Get-Content $specFile -Raw

    if ($specContent -match "ffmpeg") {
        Write-Success ".spec file exists and contains ffmpeg reference"

        Write-Info "ffmpeg-related lines:"
        Get-Content $specFile | Select-String -Pattern "ffmpeg|binaries|datas" | ForEach-Object {
            Write-Host "    $($_.Line.Trim())" -ForegroundColor Gray
        }
    } else {
        Write-Failure ".spec file exists but does NOT contain ffmpeg!"
        Write-Info "This indicates --add-binary argument was not processed correctly"
    }
} else {
    Write-Warning-Custom ".spec file not found (this is OK if build hasn't run yet)"
}

# Step 4: Verify Sidecar Binary
Write-Host "`n[Step 4] Checking Sidecar Binary..." -ForegroundColor Yellow
Write-Host "----------------------------------------"

$binaryPath = "src-tauri/binaries/vn-sidecar-x86_64-pc-windows-msvc.exe"
if (Test-Path $binaryPath) {
    $binarySize = (Get-Item $binaryPath).Length
    $binaryMB = [math]::Round($binarySize / 1MB, 2)

    Write-Info "Sidecar binary size: $binaryMB MB"

    if ($binaryMB -lt 100) {
        Write-Failure "Binary too small! Expected ~150 MB with ffmpeg"
        Write-Info "Current size ($binaryMB MB) indicates ffmpeg was NOT bundled"
    } elseif ($binaryMB -ge 130 -and $binaryMB -le 180) {
        Write-Success "Binary size looks correct (~150 MB)"
        Write-Info "Size indicates ffmpeg is likely bundled"
    } else {
        Write-Warning-Custom "Unusual binary size: $binaryMB MB"
        Write-Info "Expected: 130-180 MB (with ffmpeg)"
    }

    # Try to get file details
    $fileInfo = Get-Item $binaryPath
    Write-Info "Last modified: $($fileInfo.LastWriteTime)"

} else {
    Write-Failure "Sidecar binary not found!"
    Write-Info "Expected location: $binaryPath"
    if (-not $FullBuild) {
        Write-Info "Run with -FullBuild to build the sidecar"
    }
}

# Step 5: Runtime Verification (if binary exists)
if (Test-Path $binaryPath) {
    Write-Host "`n[Step 5] Runtime Verification..." -ForegroundColor Yellow
    Write-Host "----------------------------------------"
    Write-Info "Starting sidecar on port 9999 for 5 seconds..."

    $process = Start-Process -FilePath $binaryPath -ArgumentList "--port", "9999" -PassThru -RedirectStandardError "sidecar_test.log" -WindowStyle Hidden

    Start-Sleep -Seconds 5

    if (-not $process.HasExited) {
        Write-Success "Sidecar started successfully"

        # Kill the process
        Stop-Process -Id $process.Id -Force

        # Check logs for ffmpeg detection
        if (Test-Path "sidecar_test.log") {
            $logContent = Get-Content "sidecar_test.log" -Raw

            if ($logContent -match "\[ffmpeg\] OK Found bundled ffmpeg\.exe") {
                Write-Success "ffmpeg detected in runtime logs!"
                Write-Info "Log shows: '[ffmpeg] OK Found bundled ffmpeg.exe'"
            } elseif ($logContent -match "\[ffmpeg\] NOT FOUND") {
                Write-Failure "ffmpeg NOT found at runtime!"
                Write-Info "Sidecar will not be able to merge video formats"
                Write-Info "Log excerpt:"
                $logContent -split "`n" | Select-String "ffmpeg" | Select-Object -First 5 | ForEach-Object {
                    Write-Host "    $_" -ForegroundColor Red
                }
            } else {
                Write-Warning-Custom "Could not determine ffmpeg status from logs"
            }

            Write-Info "`nFirst 10 log lines:"
            Get-Content "sidecar_test.log" -First 10 | ForEach-Object {
                Write-Host "    $_" -ForegroundColor Gray
            }

            Remove-Item "sidecar_test.log" -ErrorAction SilentlyContinue
        }
    } else {
        Write-Failure "Sidecar failed to start or crashed immediately"
        Write-Info "Check error logs for details"
    }
}

# Summary
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Verification Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

$allGood = $true

# Check summary
if ($ffmpegOK) {
    Write-Success "ffmpeg download: OK"
} else {
    Write-Failure "ffmpeg download: FAILED"
    $allGood = $false
}

if (Test-Path $specFile) {
    $specContent = Get-Content $specFile -Raw
    if ($specContent -match "ffmpeg") {
        Write-Success ".spec file: Contains ffmpeg"
    } else {
        Write-Failure ".spec file: Missing ffmpeg reference"
        $allGood = $false
    }
} else {
    Write-Warning-Custom ".spec file: Not found (build not run?)"
}

if (Test-Path $binaryPath) {
    $binarySize = (Get-Item $binaryPath).Length / 1MB
    if ($binarySize -ge 130 -and $binarySize -le 180) {
        Write-Success "Binary size: OK ($([math]::Round($binarySize, 2)) MB)"
    } else {
        Write-Failure "Binary size: Unexpected ($([math]::Round($binarySize, 2)) MB)"
        $allGood = $false
    }
} else {
    Write-Warning-Custom "Binary: Not found"
}

Write-Host ""
if ($allGood -and (Test-Path $binaryPath)) {
    Write-Host "✓ All checks passed! Windows build appears correct." -ForegroundColor Green
} else {
    Write-Host "⚠ Some issues detected. See details above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting steps:" -ForegroundColor Cyan
    Write-Host "  1. Run: .\test_windows_build.ps1 -FullBuild" -ForegroundColor White
    Write-Host "  2. Check: WINDOWS_DEBUG_GUIDE.md" -ForegroundColor White
    Write-Host "  3. Manual build: cd src-python && python build_sidecar.py" -ForegroundColor White
}

Write-Host ""
