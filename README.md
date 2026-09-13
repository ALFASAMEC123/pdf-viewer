# PDF Viewer - Portable Windows EXE with Dark Mode

A lightweight, offline PDF viewer packaged as a single portable `.exe` file.
Features dark mode, page thumbnails, search, zoom, and fullscreen.

## Features
- 🌙 **Dark/Light mode** (Ctrl+D, persists)
- 📑 **Page sidebar** with thumbnails
- 🔍 **Text search** with highlight (Ctrl+F)
- 🔍 **Zoom** (Ctrl+/-, Ctrl+0 reset, Fit Width/Page)
- 🖥️ **Fullscreen** (F11)
- ⌨️ **Keyboard navigation** (arrows, PgUp/PgDn, Home/End)
- 📦 **Single portable EXE** - no install, runs offline
- 📄 **PDF embedded** - truly standalone

## Download
Get the latest build from [GitHub Actions artifacts](../../actions) or [Releases](../../releases).

## Build Locally
```bash
pip install -r requirements.txt
python build_exe.py
# Output: dist/pdf-viewer.exe
```

## Controls
| Key | Action |
|-----|--------|
| ← / → | Prev/Next page |
| ↑ / ↓ | Scroll |
| PgUp / PgDn | Prev/Next page |
| Home / End | First/Last page |
| Ctrl + D | Toggle dark mode |
| Ctrl + F | Search |
| F11 | Fullscreen |
| Ctrl + +/- | Zoom in/out |
| Ctrl + 0 | Reset zoom |
| Escape | Exit fullscreen / Clear search |

## Tech Stack
- Python 3.11+
- PyMuPDF (fitz) - PDF rendering
- Tkinter - GUI (stdlib)
- PyInstaller - EXE bundling