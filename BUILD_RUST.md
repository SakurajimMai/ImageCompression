# Rust 构建与验证指南

本项目当前为纯 Rust 实现，入口在 `src/main.rs`，核心模块在 `src/core/`，命令行子命令在 `src/cmd/`。旧版 Go/Wails 代码已经从工作区移除，发布构建以 Cargo 和 GitHub Actions 为准。

## 环境要求

- Rust stable，建议使用最新稳定版。
- Windows、Linux、macOS 均可构建。
- AVIF 压缩运行时需要 `avifenc`，WebP 压缩运行时需要 `cwebp`。
- Windows 本地如果 `cargo` 不在 PATH，可先执行：`$env:PATH="$env:USERPROFILE\.cargo\bin;$env:PATH"`。

## 本地构建

```powershell
cd C:\Users\sakurajiamai\Desktop\code\ImageCompression
cargo check --all-targets
cargo test --all
cargo build --release
```

发布二进制默认启用 SFTP 支持。`avifenc.exe` 可放在 `build/bin/windows-artifacts/`，设置里只需要配置该目录路径，程序会自动解析目录下的 `avifenc.exe`。

## CLI 验证

```powershell
$ICLI = ".\target\release\ImageCompression.exe"

& $ICLI --help
& $ICLI version
& $ICLI scan --input "D:\photos\raw" --json
& $ICLI prepare --input "D:\photos\raw" --output "D:\photos\prepared" --json
& $ICLI compress --input "D:\photos\prepared" --format jpeg --quality 80 --output "D:\photos\out_jpeg" --json
& $ICLI upload --input "D:\photos\out_jpeg" --json
```

`prepare`、`compress`、`upload` 都可以单独执行。上传未配置自定义路径时，会按输入目录名生成远端路径；配置自定义路径时，会追加到协议对应的远端目录或 S3 prefix。

## TUI 启动

```powershell
& $ICLI
```

无参数启动 TUI。常用键位：

- `j` / `k` 或方向键：移动选择。
- `Enter`：进入目录或确认操作。
- `Backspace`：返回上级目录。
- `r`：扫描当前目录。
- `p`：执行准备。
- `c`：执行压缩。
- `,`：打开设置。
- `q`：退出。

## GitHub Actions

仓库包含两个工作流：

- `.github/workflows/ci.yml`：push 和 PR 时运行 `cargo check --all-targets`、`cargo test --all` 和跨平台 release 构建。
- `.github/workflows/release.yml`：推送 `v*` tag 或手动触发时构建 Windows、Linux、macOS 发布包。

Release 页面会生成平台压缩包和 `sha256sums.txt`。普通用户优先下载 release 产物，无需本地 Rust 环境。

## 常见问题

- 扫描或压缩目录不存在时，命令应直接返回错误，不会再以 0 个文件静默成功。
- S3 自定义 endpoint 使用 path-style URL：`/<bucket>/<key>`，签名路径必须与实际 PUT 路径一致。
- FTP/SFTP 上传会使用配置中的代理；S3 也会把代理传给 `reqwest`。
- Windows 压缩不会批量弹出命令窗口，外部 encoder 通过隐藏进程执行。