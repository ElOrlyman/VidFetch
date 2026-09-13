from __future__ import annotations

import os
import shutil
import signal
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

import yt_dlp

APP_NAME = "VidFetch"
DEFAULT_OUTPUT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"


def app_directory() -> Path:
    """Return the directory containing the running application.

    Returns:
        Path to the application directory.
    """
    import sys

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resolve_tool(name: str) -> str | None:
    """Resolve an executable beside the app or from PATH.

    Args:
        name: Executable name without requiring an .exe suffix.

    Returns:
        Absolute executable path when found, otherwise None.
    """
    candidates = [f"{name}.exe", name] if os.name == "nt" else [name]
    base = app_directory()

    for candidate in candidates:
        local = base / candidate
        if local.exists():
            return str(local)

    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found

    return None


def format_duration(seconds: Any) -> str:
    """Convert seconds into a human-readable duration.

    Args:
        seconds: Duration in seconds.

    Returns:
        Duration formatted as HH:MM:SS or MM:SS.
    """
    if not isinstance(seconds, (int, float)):
        return "Unknown duration"

    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


class VidFetchApp(tk.Tk):
    """Tkinter desktop front end for yt-dlp."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("900x760")
        self.minsize(820, 680)

        self.cancel_event = threading.Event()
        self.active_ydl: yt_dlp.YoutubeDL | None = None

        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.mode_var = tk.StringVar(value="Video + Audio")
        self.resolution_var = tk.StringVar(value="Best")
        self.container_var = tk.StringVar(value="mp4")
        self.audio_format_var = tk.StringVar(value="mp3")
        self.audio_quality_var = tk.StringVar(value="192")
        self.rate_limit_var = tk.StringVar()
        self.fps_var = tk.StringVar(value="Any")
        self.fragments_var = tk.StringVar(value="4")
        self.subtitle_lang_var = tk.StringVar(value="en.*")
        self.playlist_var = tk.BooleanVar(value=False)
        self.metadata_var = tk.BooleanVar(value=True)
        self.thumbnail_var = tk.BooleanVar(value=False)
        self.subtitles_var = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Paste a URL and click Analyze.")
        self.media_var = tk.StringVar(value="No media analyzed yet.")
        self.dependency_var = tk.StringVar()

        self._build_ui()
        self._refresh_dependencies()
        self._update_mode_controls()

    def _build_ui(self) -> None:
        """Create and lay out the application widgets.

        Returns:
            None.
        """
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(9, weight=1)

        ttk.Label(root, text=APP_NAME, font=("Segoe UI", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(root, text="Simple desktop downloads powered by yt-dlp and FFmpeg.").grid(row=1, column=0, sticky="w", pady=(2, 14))

        url_frame = ttk.Frame(root)
        url_frame.grid(row=2, column=0, sticky="ew")
        url_frame.columnconfigure(0, weight=1)
        ttk.Entry(url_frame, textvariable=self.url_var).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(url_frame, text="Paste", command=self._paste_url).grid(row=0, column=1, padx=(0, 8))
        self.analyze_button = ttk.Button(url_frame, text="Analyze", command=self._start_analyze)
        self.analyze_button.grid(row=0, column=2)

        ttk.Label(root, textvariable=self.media_var, wraplength=840).grid(row=3, column=0, sticky="w", pady=(10, 14))

        settings = ttk.LabelFrame(root, text="Download settings", padding=12)
        settings.grid(row=4, column=0, sticky="ew")
        for column in range(4):
            settings.columnconfigure(column, weight=1)

        self.mode_combo = self._combo(settings, "Mode", self.mode_var, ["Video + Audio", "Audio only"], 0, 0)
        self.mode_combo.bind("<<ComboboxSelected>>", lambda _event: self._update_mode_controls())
        self.resolution_combo = self._combo(settings, "Resolution", self.resolution_var, ["Best"], 0, 1)
        self.container_combo = self._combo(settings, "Container", self.container_var, ["mp4", "mkv", "webm"], 0, 2)
        self.audio_combo = self._combo(settings, "Audio format", self.audio_format_var, ["mp3", "m4a", "opus", "flac", "wav"], 0, 3)
        self.quality_combo = self._combo(settings, "Audio kbps", self.audio_quality_var, ["128", "192", "256", "320"], 2, 0)
        self._entry(settings, "Rate limit (e.g. 5M)", self.rate_limit_var, 2, 1)
        self._combo(settings, "FPS cap", self.fps_var, ["Any", "30", "60"], 2, 2)
        self._combo(settings, "Parallel fragments", self.fragments_var, ["1", "2", "4", "8", "16"], 2, 3)
        self._entry(settings, "Subtitle languages", self.subtitle_lang_var, 4, 0)

        checks = ttk.Frame(settings)
        checks.grid(row=6, column=0, columnspan=4, sticky="w", pady=(12, 0))
        ttk.Checkbutton(checks, text="Allow playlist", variable=self.playlist_var).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(checks, text="Embed metadata", variable=self.metadata_var).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(checks, text="Embed thumbnail", variable=self.thumbnail_var).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(checks, text="Embed subtitles", variable=self.subtitles_var).pack(side="left")

        output = ttk.LabelFrame(root, text="Save to", padding=12)
        output.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        output.columnconfigure(0, weight=1)
        ttk.Entry(output, textvariable=self.output_var).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(output, text="Browse...", command=self._choose_folder).grid(row=0, column=1)

        progress = ttk.LabelFrame(root, text="Progress", padding=12)
        progress.grid(row=6, column=0, sticky="ew", pady=(14, 0))
        progress.columnconfigure(0, weight=1)
        ttk.Progressbar(progress, variable=self.progress_var, maximum=100).grid(row=0, column=0, sticky="ew")
        ttk.Label(progress, textvariable=self.status_var).grid(row=1, column=0, sticky="w", pady=(6, 0))

        buttons = ttk.Frame(root)
        buttons.grid(row=7, column=0, sticky="e", pady=(14, 0))
        self.download_button = ttk.Button(buttons, text="Download", command=self._start_download)
        self.download_button.pack(side="left", padx=(0, 8))
        self.cancel_button = ttk.Button(buttons, text="Cancel", command=self._cancel_download, state="disabled")
        self.cancel_button.pack(side="left")

        ttk.Label(root, textvariable=self.dependency_var).grid(row=8, column=0, sticky="w", pady=(14, 0))
        self.log = tk.Text(root, height=8, wrap="word", state="disabled")
        self.log.grid(row=9, column=0, sticky="nsew", pady=(8, 0))

    def _combo(self, parent: ttk.Widget, label: str, variable: tk.StringVar, values: list[str], row: int, column: int) -> ttk.Combobox:
        """Create a labeled readonly combobox.

        Args:
            parent: Parent widget.
            label: Field label.
            variable: Bound tkinter variable.
            values: Available values.
            row: Grid row for the label.
            column: Grid column.

        Returns:
            Created combobox.
        """
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", pady=(8 if row else 0, 0))
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        combo.grid(row=row + 1, column=column, sticky="ew", padx=(0, 8 if column < 3 else 0))
        return combo

    def _entry(self, parent: ttk.Widget, label: str, variable: tk.StringVar, row: int, column: int) -> ttk.Entry:
        """Create a labeled text entry.

        Args:
            parent: Parent widget.
            label: Field label.
            variable: Bound tkinter variable.
            row: Grid row for the label.
            column: Grid column.

        Returns:
            Created entry widget.
        """
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", pady=(8 if row else 0, 0))
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row + 1, column=column, sticky="ew", padx=(0, 8 if column < 3 else 0))
        return entry

    def _paste_url(self) -> None:
        """Paste clipboard contents into the URL field.

        Returns:
            None.
        """
        try:
            self.url_var.set(self.clipboard_get().strip())
        except tk.TclError:
            return

    def _choose_folder(self) -> None:
        """Open the output folder picker.

        Returns:
            None.
        """
        folder = filedialog.askdirectory(initialdir=self.output_var.get())
        if folder:
            self.output_var.set(folder)

    def _refresh_dependencies(self) -> None:
        """Refresh external dependency status text.

        Returns:
            None.
        """
        ffmpeg = "OK" if resolve_tool("ffmpeg") else "missing"
        deno = "OK" if resolve_tool("deno") else "not found"
        self.dependency_var.set(f"Dependencies — FFmpeg: {ffmpeg}  |  Deno: {deno}")

    def _update_mode_controls(self) -> None:
        """Enable fields that apply to the selected download mode.

        Returns:
            None.
        """
        audio_only = self.mode_var.get() == "Audio only"
        self.resolution_combo.configure(state="disabled" if audio_only else "readonly")
        self.container_combo.configure(state="disabled" if audio_only else "readonly")
        self.audio_combo.configure(state="readonly" if audio_only else "disabled")
        self.quality_combo.configure(state="readonly" if audio_only else "disabled")

    def _start_analyze(self) -> None:
        """Start media metadata extraction in a worker thread.

        Returns:
            None.
        """
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(APP_NAME, "Paste a media URL first.")
            return

        self.analyze_button.configure(state="disabled")
        self.status_var.set("Analyzing...")
        threading.Thread(target=self._analyze_worker, args=(url,), daemon=True).start()

    def _analyze_worker(self, url: str) -> None:
        """Extract media metadata and available resolutions.

        Args:
            url: Media URL to analyze.

        Returns:
            None.
        """
        options: dict[str, Any] = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": not self.playlist_var.get(),
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)

            if info is None:
                raise RuntimeError("No media information was returned.")

            formats = info.get("formats") or []
            heights = sorted({int(item["height"]) for item in formats if item.get("height") and item.get("vcodec") not in (None, "none")}, reverse=True)
            title = info.get("title") or "Untitled"
            uploader = info.get("uploader") or info.get("channel") or "Unknown creator"
            duration = format_duration(info.get("duration"))

            self.after(0, lambda: self._finish_analyze(title, uploader, duration, heights))
        except Exception as exc:  # yt-dlp raises extractor-specific exceptions
            self.after(0, lambda error=str(exc): self._analysis_failed(error))

    def _finish_analyze(self, title: str, uploader: str, duration: str, heights: list[int]) -> None:
        """Update UI after successful analysis.

        Args:
            title: Media title.
            uploader: Channel/uploader name.
            duration: Formatted media duration.
            heights: Available video heights.

        Returns:
            None.
        """
        self.resolution_combo.configure(values=["Best"] + [f"{height}p" for height in heights])
        self.resolution_var.set("Best")
        self.media_var.set(f"{title}\n{uploader} • {duration}")
        self.status_var.set(f"Found {len(heights)} video resolution(s)." if heights else "Media analyzed.")
        self.analyze_button.configure(state="normal")

    def _analysis_failed(self, error: str) -> None:
        """Handle an analysis failure.

        Args:
            error: Error message.

        Returns:
            None.
        """
        self.analyze_button.configure(state="normal")
        self.status_var.set("Analysis failed")
        messagebox.showerror(APP_NAME, error)

    def _start_download(self) -> None:
        """Validate settings and start a media download.

        Returns:
            None.
        """
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(APP_NAME, "Paste a media URL first.")
            return

        if not resolve_tool("ffmpeg"):
            messagebox.showerror(APP_NAME, "FFmpeg was not found. Install it or place ffmpeg.exe beside VidFetch.exe.")
            return

        output_dir = Path(self.output_var.get()).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Cannot create output folder:\n{exc}")
            return

        self.cancel_event.clear()
        self.progress_var.set(0)
        self.status_var.set("Starting download...")
        self._set_busy(True)
        threading.Thread(target=self._download_worker, args=(url, output_dir), daemon=True).start()

    def _build_options(self, output_dir: Path) -> dict[str, Any]:
        """Build yt-dlp options from the current GUI settings.

        Args:
            output_dir: Target download directory.

        Returns:
            yt-dlp options dictionary.
        """
        options: dict[str, Any] = {
            "outtmpl": str(output_dir / DEFAULT_OUTPUT_TEMPLATE),
            "noplaylist": not self.playlist_var.get(),
            "concurrent_fragment_downloads": int(self.fragments_var.get()),
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "no_warnings": False,
            "retries": 10,
            "fragment_retries": 10,
        }

        ffmpeg = resolve_tool("ffmpeg")
        if ffmpeg:
            options["ffmpeg_location"] = str(Path(ffmpeg).parent)

        rate = self.rate_limit_var.get().strip().upper()
        if rate:
            multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3}
            suffix = rate[-1]
            options["ratelimit"] = int(float(rate[:-1]) * multipliers[suffix]) if suffix in multipliers else int(rate)

        postprocessors: list[dict[str, Any]] = []

        if self.mode_var.get() == "Audio only":
            options["format"] = "bestaudio/best"
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.audio_format_var.get(),
                "preferredquality": self.audio_quality_var.get(),
            })
        else:
            resolution = self.resolution_var.get()
            height_filter = "" if resolution == "Best" else f"[height<={int(resolution[:-1])}]"
            fps = self.fps_var.get()
            fps_filter = "" if fps == "Any" else f"[fps<={int(fps)}]"
            options["format"] = f"bv*{height_filter}{fps_filter}+ba/b{height_filter}{fps_filter}"
            options["merge_output_format"] = self.container_var.get()

        if self.metadata_var.get():
            postprocessors.append({"key": "FFmpegMetadata"})

        if self.thumbnail_var.get():
            options["writethumbnail"] = True
            postprocessors.append({"key": "EmbedThumbnail"})

        if self.subtitles_var.get() and self.mode_var.get() != "Audio only":
            options["writesubtitles"] = True
            options["writeautomaticsub"] = True
            options["subtitleslangs"] = [self.subtitle_lang_var.get().strip() or "en.*"]
            options["embedsubtitles"] = True

        if postprocessors:
            options["postprocessors"] = postprocessors

        return options

    def _download_worker(self, url: str, output_dir: Path) -> None:
        """Run the media download in a worker thread.

        Args:
            url: Media URL.
            output_dir: Destination directory.

        Returns:
            None.
        """
        try:
            options = self._build_options(output_dir)
            with yt_dlp.YoutubeDL(options) as ydl:
                self.active_ydl = ydl
                ydl.download([url])

            if self.cancel_event.is_set():
                self.after(0, lambda: self._finish_download("Cancelled", False))
            else:
                self.after(0, lambda: self._finish_download("Download complete", True))
        except Exception as exc:  # yt-dlp raises extractor/download specific exceptions
            if self.cancel_event.is_set():
                self.after(0, lambda: self._finish_download("Cancelled", False))
            else:
                self.after(0, lambda error=str(exc): self._download_failed(error))
        finally:
            self.active_ydl = None

    def _progress_hook(self, data: dict[str, Any]) -> None:
        """Receive progress callbacks from yt-dlp.

        Args:
            data: yt-dlp progress data.

        Returns:
            None.

        Raises:
            RuntimeError: When the user cancels the active download.
        """
        if self.cancel_event.is_set():
            raise RuntimeError("Download cancelled by user")

        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            downloaded = data.get("downloaded_bytes") or 0
            percent = (downloaded / total * 100) if total else 0
            speed = data.get("speed") or 0
            eta = data.get("eta")
            speed_text = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "—"
            eta_text = f"{eta}s" if eta is not None else "—"
            self.after(0, lambda: self.progress_var.set(percent))
            self.after(0, lambda: self.status_var.set(f"{percent:.1f}% • {speed_text} • ETA {eta_text}"))
        elif status == "finished":
            self.after(0, lambda: self.status_var.set("Processing media..."))

    def _cancel_download(self) -> None:
        """Request cancellation of the active download.

        Returns:
            None.
        """
        self.cancel_event.set()
        self.status_var.set("Cancelling...")

    def _set_busy(self, busy: bool) -> None:
        """Enable or disable controls during a download.

        Args:
            busy: Whether a download is active.

        Returns:
            None.
        """
        self.download_button.configure(state="disabled" if busy else "normal")
        self.analyze_button.configure(state="disabled" if busy else "normal")
        self.cancel_button.configure(state="normal" if busy else "disabled")

    def _finish_download(self, status: str, success: bool) -> None:
        """Finish download UI state.

        Args:
            status: Completion status text.
            success: Whether the download succeeded.

        Returns:
            None.
        """
        self.status_var.set(status)
        if success:
            self.progress_var.set(100)
        self._set_busy(False)
        if success:
            messagebox.showinfo(APP_NAME, status)

    def _download_failed(self, error: str) -> None:
        """Handle a download error.

        Args:
            error: Error message.

        Returns:
            None.
        """
        self.status_var.set("Download failed")
        self._set_busy(False)
        messagebox.showerror(APP_NAME, error)


if __name__ == "__main__":
    VidFetchApp().mainloop()
