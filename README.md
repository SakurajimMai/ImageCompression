# Image Compression

**Pure Rust TUI + CLI** (pikpaktui 风格重构)。

- 采用 ratatui + crossterm 实现交互式 TUI（Miller 三列布局、键盘驱动、overlay 设置/帮助）。
- 完整 CLI 支持（scan / prepare / compress / upload / all），带 `--json` 结构化输出，便于 agent/script 使用。
- 核心功能与原实现一致：目录扫描、准备（重命名+整理）、AVIF/WebP/JPEG 压缩（支持 8 种 resize 策略）、S3/FTP/SFTP 上传 + 代理。
- 配置完全兼容 `~/.imagecompression/config.json`。

旧的 Go + Wails + React 代码已全部移除，项目现为纯 Rust。

## 快速开始

```powershell
# 构建
cargo build --release

# 拷贝到常用位置（与 skill 兼容）
mkdir -p build/bin
Copy-Item target/release/ImageCompression.exe build/bin/ImageCompression.exe -Force

# 运行 TUI（无参数）
.\build\bin\ImageCompression.exe

# 或 CLI
.\build\bin\ImageCompression.exe --help
.\build\bin\ImageCompression.exe scan --input ./photos --json
```

## 功能

- 目录扫描：识别图片、视频和其他文件，支持递归。
- 准备流程：图片/视频重命名（0001.jpg / video001.xxx 规则）、输出目录规划、批量复制。
- 图片压缩：AVIF（avifenc）、WebP（cwebp）、JPEG（Rust image crate）。
- 缩放策略：none / width / height / percent / long_edge / short_edge / fit / fill / exact。
- 上传：S3、FTP、SFTP，支持 SOCKS5 / HTTP CONNECT 代理 + 用户名密码。
- 配置：`~/.imagecompression/config.json`（TUI 内可编辑保存）。

## 环境要求

| 依赖 | 说明 |
| --- | --- |
| Rust (最新 stable) | 构建 TUI/CLI |
| avifenc | AVIF 压缩需要（PATH 或 --avifenc 指定目录） |
| cwebp | WebP 压缩需要（PATH） |

## 构建 & 发布

本地构建：
```powershell
cargo build --release
# Windows 产物为 ImageCompression.exe
```

**自动发布**：推送 `v*` tag 到 GitHub Releases（通过 GitHub Actions）会自动构建并发布多平台预构建二进制（Windows x86_64 / ARM64、Linux x86_64 / aarch64、macOS Intel / Apple Silicon），并附带 `sha256sums.txt`。

Windows release 包会从 [AOMediaCodec/libavif](https://github.com/AOMediaCodec/libavif/releases) 官方 Release 下载 `windows-artifacts.zip`，随包附带 `avifenc.exe`、`avifdec.exe`、`avifgainmaputil.exe` 和 `libavif-version.txt`。这些二进制不提交到源码仓库；升级 AVIF 工具时只需要更新 `.github/workflows/release.yml` 中的 `LIBAVIF_VERSION`。

Release profile 已优化（lto, strip, opt-level=s）。

详见 `.github/workflows/release.yml` 和 BUILD_RUST.md。

更多验证和 TUI 操作说明见 [BUILD_RUST.md](BUILD_RUST.md)。

## 开发命令

```powershell
cargo fmt -- --check
cargo check --all-targets
cargo test --all
```

```powershell
cargo build --release
```

构建产物位于：

```text
build/bin/ImageCompression.exe
```

## 项目结构

```text
.
├── Cargo.toml
├── Cargo.lock
├── src/
│   ├── main.rs            # TUI/CLI 入口
│   ├── cmd/               # scan / prepare / compress / upload / all 子命令
│   ├── core/              # 扫描、准备、压缩、上传、工作流
│   ├── config.rs          # 配置加载、保存和兼容
│   ├── theme.rs           # TUI 主题
│   └── tui/               # ratatui 界面
├── skills/image-compression/
│   └── SKILL.md           # agent 调用说明
└── .github/workflows/
    ├── ci.yml
    └── release.yml
```

## 配置

应用配置保存在用户目录：

```text
%USERPROFILE%\.imagecompression\config.json
```

代理配置以结构化字段为准：

- `type`: `socks5` 或 `http`
- `host`: 代理主机
- `port`: 代理端口
- `username`: 可选用户名
- `password`: 可选密码

旧配置里的 `url` 字段只用于兼容加载旧数据；保存和实际上传时以前端结构化字段为准。

## CI

GitHub Actions 会执行格式检查、`cargo check --all-targets`、`cargo test --all`，并在 tag 发布时构建多平台 release 产物。
