# ImageCompression — 项目文档

纯 Rust 的 TUI + CLI 工具,用于**扫描、整理、压缩、上传**图片集合。
这是旧版 Go + Wails + React 实现的继任者;交互界面**参考 pikpaktui 风格**。

> 版本:`0.2.1`(参见 `Cargo.toml`)。许可证:Apache-2.0。

## 项目定位

ImageCompression 是一个二进制单文件工具,把摄影爱好者与图片归档人员每天
重复的繁琐操作自动化:

1. **扫描**目录,把文件分类为图片 / 视频 / 其他。
2. **整理**(prepare)目录:按稳定的命名规则(`0001.jpg`、`video001.mp4` …)
   重命名文件,并复制到组织好的输出目录树。
3. **压缩**所有图片——支持 AVIF、WebP 或 JPEG——提供八种缩放模式和完整的
   质量 / 速度 / 元数据控制。
4. **上传**结果到 S3、FTP 或 SFTP,可选用 SOCKS5 或 HTTP-CONNECT 代理。

它既可以**作为交互式 TUI** 运行(三列 Miller 布局、键盘驱动、可叠加的
设置与帮助界面),也可以**作为非交互式 CLI** 运行,带结构化 `--json`
事件输出,便于 AI Agent 逐行解析。

## 主要特性

| 能力 | 详情 |
| --- | --- |
| 目录扫描 | 递归扫描,分类为图片 / 视频 / 其他,自然排序 |
| 整理流水线 | 重命名 + 复制,冲突检测,镜像子目录结构 |
| 压缩 | AVIF(`avifenc`)、WebP(`cwebp`)、JPEG(纯 Rust `image` crate) |
| 缩放模式 | `none`、`width`、`height`、`percent`、`long_edge`、`short_edge`、`fit`、`fill`、`exact` |
| 上传协议 | S3(SigV4,自定义 endpoint,path-style)、FTP(`suppaftp`)、SFTP(`ssh2`,可选 feature) |
| 代理支持 | SOCKS5(支持账号密码)与 HTTP-CONNECT 用于 FTP/SFTP;S3 通过 `reqwest::Proxy` |
| 配置 | `~/.imagecompression/config.json` —— 完全兼容旧版 Go 构建 |
| TUI | ratatui + crossterm,三列 Miller 布局,旋转 spinner,异步后台任务,设置 overlay |
| CLI | `--json` 事件流,确定性退出码 |

## 快速开始

```powershell
# 构建(Windows;Linux/macOS 跳过最后一步 Copy-Item)
cargo build --release
mkdir -p build/bin
Copy-Item target/release/ImageCompression.exe build/bin/ImageCompression.exe -Force

# 启动 TUI(无参数)
.\build\bin\ImageCompression.exe

# 一次性 CLI 工作流
.\build\bin\ImageCompression.exe --help
.\build\bin\ImageCompression.exe scan --input ./photos
.\build\bin\ImageCompression.exe --json all --input ./photos --format avif --quality 35 --upload
```

## 环境要求

| 依赖 | 用途 |
| --- | --- |
| Rust(stable) | 构建 TUI/CLI |
| `avifenc`(libavif) | AVIF 压缩必需 —— 放入 `PATH` 或通过 `--avifenc <dir>` / `avifenc_path` 指定 |
| `cwebp` | WebP 压缩必需 —— 从 `PATH` 中查找 |

在 Linux 上使用默认 `sftp` feature 时还需要 OpenSSL 开发头文件;
`--no-default-features --features sftp-vendored-openssl` 可以避免这个要求,
代价是 OpenSSL 被静态编译进二进制。

## 下一步读什么?

| 想了解…… | 阅读 |
| --- | --- |
| 系统整体架构 | **[ARCHITECTURE.md](./ARCHITECTURE.md)** |
| 配置开发环境、运行测试、新增功能 | **[DEVELOPMENT.md](./DEVELOPMENT.md)** |
| 使用 CLI 或 JSON 事件协议 | **[API.md](./API.md)** |
| 构建发布包、运行 CI/CD | **[DEPLOYMENT.md](./DEPLOYMENT.md)** |
| 提交代码、遵循项目规范 | **[CONTRIBUTING.md](./CONTRIBUTING.md)** |

## 项目结构

```text
.
├── Cargo.toml
├── Cargo.lock
├── src/
│   ├── main.rs            # TUI/CLI 入口(按子命令分发)
│   ├── config.rs          # 配置结构、加载/保存、代理归一化
│   ├── theme.rs           # TUI 文件类型图标
│   ├── cmd/               # 每个 CLI 子命令一个文件
│   ├── core/              # 扫描 / 整理 / 压缩 / 上传 / 工作流
│   └── tui/               # ratatui + crossterm 交互界面
├── skills/image-compression/
│   └── SKILL.md           # agent 面向的使用说明
└── .github/workflows/
    ├── ci.yml             # lint + test + 跨平台构建
    └── release.yml        # tag 驱动的多平台发布(含 libavif)
```