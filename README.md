# VidFetch

VidFetch is a small Windows desktop media downloader powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and FFmpeg.

It provides a simple GUI for analyzing a media URL, choosing a resolution or audio format, and downloading the result without having to remember yt-dlp command-line options.

> Use VidFetch only for media you own, public-domain media, or content you otherwise have permission to download. You are responsible for complying with the source site's terms and applicable law.

## Features

- Analyze supported media URLs before downloading
- Detect available video resolutions
- Best-quality or resolution-capped downloads
- MP4, MKV, and WebM output
- Audio-only downloads to MP3, M4A, Opus, FLAC, or WAV
- Configurable audio quality
- Optional frame-rate cap
- Optional download rate limit
- Configurable concurrent fragments
- Playlist toggle
- Metadata, thumbnail, and subtitle embedding
- Download progress, speed, ETA, and cancellation
- Windows `.exe` builds through GitHub Actions

## Requirements

### Running from source

- Python 3.11+
- FFmpeg / FFprobe
- A JavaScript runtime supported by yt-dlp is recommended for current YouTube support; Deno is the recommended option.

Install Python dependencies:

```powershell
py -m pip install -r requirements.txt
```

Run the app:

```powershell
py vidfetch.py
```

### Windows dependencies

Using WinGet:

```powershell
winget install Gyan.FFmpeg
winget install DenoLand.Deno
```

Verify:

```powershell
ffmpeg -version
deno --version
```

VidFetch looks for `ffmpeg.exe`, `ffprobe.exe`, and `deno.exe` beside the application first, then falls back to `PATH`.

## Build a Windows executable

Install the development requirements:

```powershell
py -m pip install -r requirements-dev.txt
```

Then run:

```powershell
./build.ps1
```

The executable will be created at:

```text
dist/VidFetch.exe
```

## Portable folder

A convenient portable distribution can look like this:

```text
VidFetch/
├── VidFetch.exe
├── ffmpeg.exe
├── ffprobe.exe
└── deno.exe
```

FFmpeg and Deno are not redistributed by this repository. Download them from their official sources and review their respective licenses before redistribution.

## GitHub Actions

`.github/workflows/build-windows.yml` builds `VidFetch.exe` on pushes to `main`, pull requests, and version tags. The executable is uploaded as a workflow artifact.

## Project status

Early-stage utility. Expect UI and packaging changes while the first stable release is being prepared.
