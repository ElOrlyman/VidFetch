$ErrorActionPreference = "Stop"

Write-Host "Installing build dependencies..."
py -m pip install --upgrade pip
py -m pip install -r requirements-dev.txt

Write-Host "Cleaning previous build output..."
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Remove-Item -Force VidFetch.spec -ErrorAction SilentlyContinue

Write-Host "Building VidFetch.exe..."
pyinstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name VidFetch `
    --collect-all yt_dlp `
    vidfetch.py

Write-Host "Build complete: dist\VidFetch.exe"
