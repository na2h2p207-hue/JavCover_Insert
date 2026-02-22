# Mosaic Rename (JavCover)

Automated tool for renaming JAV video files — fetches Japanese titles from JavTrailers, downloads cover art, and embeds it into MP4 metadata.

Now with **JavCover** GUI — just double-click the `.exe` to use, no Python required.

## 📦 Download

Go to [Releases](https://github.com/na2h2p207-hue/JavCover_Insert/releases) to download the latest `JavCover.exe`. Run it directly — no installation needed.

## Features

- **Auto Rename**: Extract code from filename, fetch Japanese title, rename to `CODE Title.mp4`
- **Cover Embedding**: Download cover art, crop right half, embed into MP4 metadata
- **GUI Application**: PyWebView-powered desktop GUI with light/dark theme toggle
- **Batch / Single File**: Support folder batch processing and single-file manual fix

## Screenshots

### Light Theme
![Light Theme](images/light.jpg)

### Dark Theme
![Dark Theme](images/dark.jpg)

## Project Structure

```
├── JavCover_WebView.py     # GUI entry point (PyWebView)
├── gui/
│   ├── index.html          # Frontend structure
│   ├── style.css           # Styles (with Liquid Glass effect)
│   └── script.js           # Frontend logic
├── rename/
│   ├── rename_movies.py    # Core renaming logic
│   ├── manual_fix.py       # Single-file manual fix
│   └── faststart.py        # FFmpeg faststart utility
└── archive/
    └── build_artifacts/
        └── JavCover.spec   # PyInstaller build config
```

## CLI Usage

You can also use the tools from the command line without the GUI:

### Batch Processing

```powershell
# Dry run (preview)
python rename/rename_movies.py --dir "H:\Videos" --dry-run

# Live mode
python rename/rename_movies.py --dir "H:\Videos"
```

### Manual Fix Single File

```powershell
python rename/manual_fix.py "path\to\video.mp4"
```

## Dependencies

Only needed when running from source:

```bash
pip install pywebview pythonnet cloudscraper mutagen Pillow requests
```

## Code Formats

| Format | Example |
|--------|---------|
| Standard | `ABW-009`, `IPTD-764` |
| No hyphen | `iptd00764` → `IPTD-764` |
| DV series | `DV-1234` (4 digits) |

## License

This project is for personal and educational use only.
