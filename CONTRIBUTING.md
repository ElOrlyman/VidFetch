# Contributing to VidFetch

Thanks for helping improve VidFetch.

VidFetch is intended to stay small, understandable, and easy to use. Contributions that improve reliability, compatibility, accessibility, packaging, or the desktop experience are welcome.

## Before you start

For significant changes, open an issue first so the proposed direction can be discussed before you spend time implementing it.

For small bug fixes, documentation changes, or straightforward improvements, a pull request is fine.

## Development setup

Requirements:

- Windows 10 or Windows 11
- Python 3.11+
- FFmpeg / FFprobe
- Deno is recommended for current yt-dlp JavaScript challenge support

Clone the repository:

```powershell
git clone https://github.com/ElOrlyman/VidFetch.git
cd VidFetch
```

Create a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
py -m pip install -r requirements-dev.txt
```

Run the application:

```powershell
py vidfetch.py
```

## Branches

Create a focused branch from `main`:

```powershell
git checkout main
git pull
git checkout -b feature/my-change
```

Use short branch names that describe the change, for example:

```text
feature/dark-mode
feature/download-queue
fix/progress-parsing
docs/setup-guide
```

## Code guidelines

- Keep changes focused and easy to review.
- Prefer clear code over clever code.
- Avoid adding dependencies unless they provide meaningful value.
- Keep long-running work off the Tkinter UI thread.
- Do not introduce site-specific circumvention logic into VidFetch when that behavior belongs upstream in yt-dlp.
- Preserve compatibility with the packaged Windows application.
- Include docstrings for new functions and module-level variables where appropriate.
- Avoid committing generated executables, build folders, virtual environments, downloaded media, or local configuration.

## Testing changes

At minimum, verify that:

1. The application starts successfully.
2. URL analysis does not block the UI.
3. Resolution detection still works for a supported test URL.
4. Video and audio-only modes build valid yt-dlp options.
5. Progress updates are displayed correctly.
6. Cancellation does not leave the UI permanently disabled.
7. The application still builds with PyInstaller.

Build locally with:

```powershell
.\build.ps1
```

Then launch:

```text
dist\VidFetch.exe
```

## Pull requests

A good pull request should include:

- A concise explanation of the problem
- What changed
- How you tested it
- Screenshots for visible UI changes when useful
- Any compatibility or dependency implications

Keep unrelated refactoring out of feature and bug-fix pull requests whenever possible.

## Bug reports

Please include:

- VidFetch version or commit
- Windows version
- Python version when running from source
- yt-dlp version
- FFmpeg version when relevant
- A reproducible URL when it is safe and appropriate to share
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error output or screenshots

Do not include passwords, authentication cookies, tokens, private URLs, or other secrets in issues.

## Feature requests

Explain the user problem first, then describe the proposed solution. If the feature maps directly to an existing yt-dlp option, include the relevant option name when known.

## Responsible use

Contributions must not turn VidFetch into a tool specifically designed to bypass access controls, DRM, paywalls, or other technical protections.

VidFetch should remain a general-purpose interface for media that users have permission or a legal right to download.

## License

By contributing to VidFetch, you agree that your contributions will be licensed under the project's MIT License.
