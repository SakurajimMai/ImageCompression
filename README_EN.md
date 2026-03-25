# Image Compression

> High-Performance Batch Image Compression Platform — GUI + CLI

**English** | [中文](./README.md)

## ✨ Features

| Feature | Description |
|---|---|
| 🖼️ Multi-format | Input: JPG/PNG/WebP/HEIC/TIFF/BMP/GIF/AVIF — Output: AVIF/WebP/JPEG |
| ⚡ High Performance | Parallel processing + avifenc native multi-threading + real-time speed |
| 📐 Full AVIF Control | YUV 420/422/444 · Bit depth 8/10/12 · Alpha quality · Lossless · Progressive |
| 🎯 Presets | web / mobile / lossless / max_compress / hdr one-click presets |
| 📁 Batch Processing | Recursive subdirectories · Preserve structure · Skip/Overwrite/Rename conflicts |
| 🔍 Preview | Side-by-side before/after comparison |
| ☁️ Cloud Upload | S3 / FTP / SFTP · Custom domain · Recursive · Proxy support |
| 🎨 Themes | Light / Dark / Gray |
| 🌐 i18n | Chinese / English interface |

---

## 📦 Installation

### Requirements

- **Python** 3.11+
- **avifenc** (libavif) — Required for AVIF compression

### Step 1: Install avifenc

```bash
# Windows (scoop recommended)
scoop install libavif

# Windows (manual)
# Download from https://github.com/AOM-AV1-Codec/libavif/releases
# Place avifenc.exe in PATH or configure path in Settings

# macOS
brew install libavif

# Linux (Ubuntu/Debian)
apt install libavif-bin

# Linux (Arch)
pacman -S libavif
```

### Step 2: Install Dependencies

```bash
git clone <repo-url>
cd ImageCompression
pip install -r requirements.txt
```

### Step 3: Launch

```bash
# GUI mode
cd src
python main.py

# CLI mode
python cli.py --help
```

---

## 🖥️ GUI Guide

### Tabs

| Tab | Function |
|---|---|
| **Prepare** | File renaming + directory organization (recursive, per-subdir numbering) |
| **Compress** | Core compression: AVIF/WebP/JPEG |
| **Upload** | Upload compressed files to S3/FTP/SFTP |
| **Settings** | avifenc path · Theme · Language |
| **Help** | Built-in documentation |

### AVIF Parameters

| Parameter | Range | Default | Description |
|---|---|---|---|
| Quality Min | 0-63 | 20 | avifenc `--min`, lower = more compression |
| Quality Max | 0-63 | 40 | avifenc `--max`, determines final quality |
| Speed | 0-10 | 6 | 0=slowest/best, 10=fastest |
| Threads | 1-N / All | All | Encoding thread count |
| YUV | 420/422/444 | 420 | 420=smallest, 444=highest quality |
| Bit Depth | 8/10/12 | 8 | 8=standard, 10=HDR, 12=professional |
| Alpha Quality | Optional | Off | Independent alpha channel control |
| Lossless | On/Off | Off | Lossless mode, larger files |
| Progressive | On/Off | Off | Progressive loading (libavif 1.1+) |

### WebP / JPEG Parameters

| Parameter | Range | Default | Description |
|---|---|---|---|
| Quality | 1-100 | 80 | Compression quality |
| Lossless (WebP) | On/Off | Off | WebP only |

### Resize Modes

| Mode | Description |
|---|---|
| None | Keep original resolution |
| Width | Fixed width, proportional height |
| Height | Fixed height, proportional width |
| Percent | Scale by percentage (e.g., 50%) |
| Long Edge | Limit longest edge, proportional scaling |
| Short Edge | Limit shortest edge, proportional scaling |

> ⚠️ **Note**: All resize modes use proportional scaling — images are **never cropped**.

### AVIF Quality Reference

| AVIF Quality Max | ≈ JPEG Equivalent | Use Case |
|:---:|:---:|:---|
| 60-63 | 95+ | Archival, print |
| 45-55 | 85-92 | High-quality web |
| 35-45 | 75-85 | General web |
| 25-35 | 65-75 | Thumbnails, mobile |
| 15-25 | 50-65 | Maximum compression |

---

## ⌨️ CLI Guide

### Basic Usage

```bash
# Default AVIF compression
python cli.py compress ./photos -o ./output

# Specify format and quality
python cli.py compress ./photos -f avif -q 40 -o ./output

# Use preset
python cli.py compress ./photos --preset web

# Recursive + overwrite
python cli.py compress ./photos -f avif --recursive --overwrite

# Custom avifenc path
python cli.py compress ./photos --avifenc /path/to/avifenc

# Lossless + HDR
python cli.py compress ./photos --lossless --depth 10 --yuv 444
```

### Other Commands

```bash
# Image info
python cli.py info photo.jpg

# Scan directory
python cli.py scan ./photos -r

# List presets
python cli.py presets
```

### CLI Options

| Option | Short | Description |
|---|---|---|
| `--format` | `-f` | Output format: avif / webp / jpeg |
| `--output` | `-o` | Output directory |
| `--quality` | `-q` | Quality (0-100) |
| `--speed` | `-s` | AVIF speed (0-10) |
| `--preset` | | Preset template |
| `--lossless` | | Lossless mode |
| `--recursive` | `-r` | Recursive subdirectories |
| `--overwrite` | | Overwrite original files |
| `--workers` | `-j` | Parallel workers |
| `--yuv` | | YUV format (420/422/444) |
| `--depth` | | Bit depth (8/10/12) |
| `--avifenc` | | avifenc binary path |

---

## 📋 Presets

| Preset | Quality | Speed | YUV | Depth | Description |
|---|---|---|---|---|---|
| `web` | 55 | 6 | 420 | 8 | Web display, balanced |
| `mobile` | 60 | 6 | 420 | 8 | Mobile optimized |
| `lossless` | 100 | 4 | 444 | 10 | Lossless |
| `max_compress` | 30 | 4 | 420 | 8 | Maximum compression |
| `hdr` | 65 | 4 | 444 | 10 | HDR mode |

---

## ☁️ Upload Configuration

### SFTP

| Field | Description | Example |
|---|---|---|
| Host | Server address | `192.168.1.100` |
| Port | SSH port | `22` |
| Username | SSH user | `deploy` |
| Password / Key | Authentication | — |
| Remote Dir | Absolute upload path | `/var/www/uploads/xxxx` |
| Domain | CDN or website domain | `https://cdn.example.com` |
| Domain Root | Server path mapped to domain | `/var/www` |

**URL Formula**: `Domain` + (`Remote Dir` - `Domain Root`) + `/filename`

Example: `https://cdn.example.com/uploads/xxxx/0001.avif`

### S3

| Field | Description |
|---|---|
| Endpoint | S3 endpoint URL |
| Bucket | Bucket name |
| Access Key | Access key |
| Secret Key | Secret key |
| Prefix | Remote path prefix |
| Custom Domain | CDN domain (optional) |

---

## 📂 Project Structure

```
ImageCompression/
├── src/
│   ├── main.py              # GUI entry
│   ├── cli.py               # CLI entry (click)
│   ├── config.py            # Config management (JSON)
│   ├── core/                # Business logic
│   │   ├── compress.py      # Compression
│   │   ├── prepare.py       # File preparation
│   │   └── upload.py        # Upload (S3/FTP/SFTP)
│   ├── engine/              # Core engine
│   │   ├── formats/         # Format handler plugins
│   │   │   ├── base.py      # FormatHandler ABC
│   │   │   ├── registry.py  # Auto-discovery registry
│   │   │   ├── avif.py      # AVIF (avifenc)
│   │   │   ├── webp.py      # WebP (Pillow)
│   │   │   └── jpeg.py      # JPEG (Pillow)
│   │   ├── pipeline.py      # Batch scheduler
│   │   ├── scanner.py       # Directory scanner
│   │   ├── presets.py       # Preset templates
│   │   └── resizer.py       # Resize engine
│   └── ui/                  # PySide6 GUI
│       ├── main_window.py   # Main window
│       ├── compress_tab.py  # Compression tab
│       ├── upload_tab.py    # Upload tab
│       ├── theme.py         # Theme system
│       └── i18n.py          # Internationalization
├── tests/                   # Tests (54 cases)
├── docs/                    # Documentation
└── requirements.txt
```

## 🔧 Tech Stack

| Component | Technology |
|---|---|
| GUI | PySide6 (Qt6) |
| CLI | click |
| AVIF Encoding | avifenc (libavif) |
| Image Processing | Pillow + pillow-heif |
| Cloud Upload | boto3 (S3) · paramiko (SFTP) · ftplib (FTP) |
| Config | JSON (dataclass) |

## 📄 License

MIT License
