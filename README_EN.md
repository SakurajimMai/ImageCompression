# Image Compression

**Pure Rust TUI + CLI** (inspired by pikpaktui style and layout).

- ratatui + crossterm interactive TUI with Miller three-column layout and keyboard-driven navigation.
- Full-featured CLI (scan/prepare/compress/upload/all) with `--json` structured output for agents/scripts.
- Core features preserved 1:1: directory scan, prepare (renaming + copy), AVIF/WebP/JPEG compression with 8 resize strategies, S3/FTP/SFTP upload + proxies.
- Fully compatible with `~/.imagecompression/config.json`.

All old Go + Wails + React code has been removed. This is now a pure Rust project.

## Quick Start

```powershell
cargo build --release
mkdir -p build/bin
Copy-Item target/release/ImageCompression.exe build/bin/ImageCompression.exe -Force

# Launch TUI
build/bin/ImageCompression.exe

# Or use CLI
build/bin/ImageCompression.exe --help
build/bin/ImageCompression.exe scan --input ./photos --json
```

See BUILD_RUST.md for detailed Chinese build & verification guide.

## Features

- Directory scanning (images/videos/others, recursive).
- Prepare workflow: rename (0001.jpg / video001.xxx per subdir), organize to output dir, copy.
- Compression: AVIF (via avifenc), WebP (via cwebp), JPEG (pure Rust image crate).
- Resize strategies: none, width, height, percent, long_edge, short_edge, fit, fill, exact.
- Upload: S3, FTP, SFTP with SOCKS5/HTTP CONNECT proxy support (username/password).
- Config: `~/.imagecompression/config.json` (editable from TUI).

## Requirements

| Dependency | Purpose |
| --- | --- |
| Rust (stable) | Build TUI & CLI |
| avifenc | Required for AVIF (in PATH or via --avifenc) |
| cwebp | Required for WebP (in PATH) |

## Build

Local build:
```powershell
cargo build --release
```

**Automated releases**: Pushing a tag (e.g. `git tag v0.2.0 && git push --tags`) triggers GitHub Actions to build and publish pre-built binaries for Windows (x86_64 + aarch64), Linux (x86_64 + aarch64), macOS (Intel + Apple Silicon), plus `sha256sums.txt`.

The release profile uses LTO, stripping, and size optimizations.

See `.github/workflows/release.yml` and BUILD_RUST.md for details.

## Commands

```powershell
cargo fmt -- --check
cargo check --all-targets
cargo test --all
```

```powershell
cargo build --release
```

The Windows executable is generated at:

```text
build/bin/ImageCompression.exe
```

## Structure

```text
.
├── Cargo.toml
├── Cargo.lock
├── src/
│   ├── main.rs
│   ├── cmd/
│   ├── core/
│   ├── config.rs
│   ├── theme.rs
│   └── tui/
├── build/bin/windows-artifacts/
│   ├── avifenc.exe
│   ├── avifdec.exe
│   └── avifgainmaputil.exe
├── skills/image-compression/
│   └── SKILL.md
└── .github/workflows/
    ├── ci.yml
    └── release.yml
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

## CI

GitHub Actions runs formatting checks, `cargo check --all-targets`, `cargo test --all`, and builds multi-platform release artifacts on tags.
