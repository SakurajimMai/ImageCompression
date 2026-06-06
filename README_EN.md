# Image Compression

Image Compression is a Go + Wails + React/Vite desktop workbench for preparing, compressing, and uploading image assets. The repository now keeps only the Go/Wails implementation; the old Python/PySide6 implementation has been removed.

## Features

- Directory scanning with optional recursion.
- Prepare workflow for renaming and copying image/video files.
- AVIF, WebP, and JPEG compression.
- Resize modes: none, width, height, percent, long edge, short edge, fit, fill, and exact.
- S3, FTP, and SFTP uploads.
- Upload proxy support for SOCKS5 and HTTP CONNECT, including username/password authentication.
- Windows single-exe desktop build through Wails.

## Requirements

| Dependency | Purpose |
| --- | --- |
| Go 1.23+ | Backend core and Wails build |
| Node.js 22+ | React/Vite frontend build |
| Wails v2.10.2 | Desktop application build |
| avifenc | AVIF encoding |
| cwebp | WebP encoding |

JPEG encoding is handled by the Go standard library.

## Commands

```powershell
Push-Location frontend
npm install
npm run build
Pop-Location
```

```powershell
go test ./...
```

```powershell
go run github.com/wailsapp/wails/v2/cmd/wails@v2.10.2 build
```

Or install the Wails CLI first:

```powershell
go install github.com/wailsapp/wails/v2/cmd/wails@v2.10.2
wails build
```

The Windows executable is generated at:

```text
build/bin/ImageCompression.exe
```

## Structure

```text
.
├── app.go
├── main.go
├── go.mod
├── go.sum
├── wails.json
├── internal/
│   ├── compress/
│   ├── config/
│   ├── core/
│   ├── prepare/
│   ├── upload/
│   └── workflow/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── package-lock.json
├── docs/
│   └── GO_WAILS_REWRITE.md
└── .github/workflows/
    └── build.yml
```

## Configuration

The application stores its config at:

```text
%USERPROFILE%\.imagecompression\config.json
```

Proxy settings use structured fields:

- `type`: `socks5` or `http`
- `host`
- `port`
- `username`
- `password`

The legacy `url` field is only used for compatibility when loading older config files.
