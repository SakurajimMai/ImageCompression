# 部署

如何构建、打包和发布 ImageCompression —— 包括从本地机器和通过 GitHub
Actions 流水线。

## 本地构建

### 快速构建

```bash
cargo build --release
```

产物:

- Windows:`target/release/ImageCompression.exe`
- macOS / Linux:`target/release/ImageCompression`

Release profile 在 `Cargo.toml:46` 中调优:

| 设置 | 值 | 原因 |
| --- | --- | --- |
| `codegen-units` | `1` | 最大化跨模块优化。 |
| `lto` | `true` | 全程序链接时优化。 |
| `opt-level` | `"s"` | 偏向小体积。 |
| `strip` | `true` | 移除符号和调试信息。 |
| `panic` | `"abort"` | 代码更小,无需 unwind 表。 |

### 拷贝到约定的 skill 路径

agent 面向的 skill(`skills/image-compression/SKILL.md`)指向
`build/bin/ImageCompression.exe`。对齐:

```powershell
mkdir -p build/bin
Copy-Item target/release/ImageCompression.exe build/bin/ImageCompression.exe -Force
```

### 用 vendored OpenSSL 构建(Linux/macOS)

当发布给没有合适 OpenSSL 版本的发行版时,可以跳过系统 OpenSSL 要求:

```bash
cargo build --release --no-default-features --features sftp-vendored-openssl
```

### 彻底关闭 SFTP

如果你根本不需要 SFTP,可以丢掉 `ssh2` 依赖:

```bash
cargo build --release --no-default-features
```

这会生成一个二进制,在被请求 SFTP 时返回清晰的 "未启用 sftp feature"
错误,而不是带着 SSH 依赖。

## CI

`.github/workflows/ci.yml` 在每次 push 和对 `main` / `master` 的 PR 上运行:

| 任务 | 内容 |
| --- | --- |
| `check` | 在 Ubuntu 上 `cargo check --all-targets`。 |
| `test` | 在 Ubuntu 上 `cargo test --all`。 |
| `build` | 跨平台(Ubuntu、macOS、Windows)`cargo build --release`,把二进制作为 `imagecompression-<OS>` artifact 上传。 |

构建任务在需要时通过 `apt-get`(Linux)或 `brew`(macOS)安装本地依赖;
Windows 使用默认的 MSVC 工具链。

## 发布流水线

`.github/workflows/release.yml` 是 tag 驱动的发布:

### 触发

- `git tag vX.Y.Z && git push --tags` —— 完整发布。
- 手动触发(`workflow_dispatch`)—— 用同一矩阵重跑。

### 矩阵

| Target | OS | 归档 | 备注 |
| --- | --- | --- | --- |
| `x86_64-pc-windows-msvc` | `windows-latest` | `zip` | 内置 libavif CLI 工具。 |
| `aarch64-pc-windows-msvc` | `windows-latest` | `zip` | 内置 libavif CLI 工具。 |
| `x86_64-unknown-linux-gnu` | `ubuntu-latest` | `tar.gz` | — |
| `aarch64-unknown-linux-gnu` | `ubuntu-latest` | `tar.gz` | 用 `cross` 构建;vendored OpenSSL。 |
| `x86_64-apple-darwin` | `macos-13` | `tar.gz` | Vendored OpenSSL。 |
| `aarch64-apple-darwin` | `macos-latest` | `tar.gz` | Vendored OpenSSL。 |

### 在 Windows 上打包 libavif

对两个 Windows target,工作流会从
[AOMediaCodec/libavif](https://github.com/AOMediaCodec/libavif/releases)
下载对应版本的 `windows-artifacts.zip`,版本由环境变量 `LIBAVIF_VERSION`
钉住(撰写时为 `v1.4.1`)。以下二进制会被放到 `windows-artifacts/`:

- `avifenc.exe`
- `avifdec.exe`
- `avifgainmaputil.exe`
- `libavif-version.txt`

这些二进制**不入源码** —— 它们只存在于发布归档中。要升级,修改
`.github/workflows/release.yml` 中的 `LIBAVIF_VERSION`,然后推送一个 tag。

### 归档布局

每个归档包含:

| 文件 | 位置 |
| --- | --- |
| `imagecompression`(或 `ImageCompression.exe`) | 根目录 |
| `windows-artifacts/` | 仅 Windows 归档 |

### 校验和

所有构建完成后,`release` 任务:

1. 下载每个 artifact。
2. 运行 `sha256sum * > sha256sums.txt`。
3. 用 tag 名作为标题创建 GitHub Release。
4. 生成 release notes,包含 libavif 来源 / changelog 链接,并上传所有
   归档 + `sha256sums.txt`。

release notes 还会通过 `gh release view` 拉取并附带 libavif 上游发布
正文。

## 跨平台要点

### Linux

- `aarch64-unknown-linux-gnu` 用 `cross` 构建,因为 GitHub 托管 runner 没有
  自带跨编译工具链;`cross` 底层用 Docker。
- `x86_64` 在 `ubuntu-latest` 上原生构建。

### macOS

- Intel(`macos-13`)与 Apple Silicon(`macos-latest`)构建都用 vendored
  OpenSSL,以避开 runner 自带 OpenSSL 的版本差异。
- `brew install pkg-config openssl zlib` 仅在非 vendored 构建时运行。

### Windows

- 默认 MSVC 工具链;除 `aarch64-pc-windows-msvc` 之外不需要额外的 Rust target。
- libavif 官方 Windows artifacts 自带的 AV1 + AVIF 编码器无需额外运行时 DLL。

## 验证发布包

下载归档后:

```bash
# Linux
tar -xzf imagecompression-x86_64-linux.tar.gz
./imagecompression version
./imagecompression --help

# macOS(如需,允许 Gatekeeper)
xattr -d com.apple.quarantine imagecompression
./imagecompression version

# Windows(PowerShell)
Expand-Archive imagecompression-x86_64-windows.zip -DestinationPath .
.\ImageCompression.exe version
```

用 `sha256sums.txt` 校验:

```bash
sha256sum -c sha256sums.txt
```

## 仅源码 checkout(无二进制)

如果只有源码仓库、想在本地构建,见 [DEVELOPMENT.md](./DEVELOPMENT.md)
了解前置依赖(Rust、`avifenc`、`cwebp`,以及启用默认 `sftp` feature 时
的 OpenSSL 开发头文件)。

想在本地开发拿到内置 libavif CLI 工具,从 GitHub Releases 下载官方
Windows 归档,把 `windows-artifacts/` 解压到 `build/bin/`,然后让
`avifenc_path` 指向该目录。

## 故障排查

| 现象 | 可能原因 | 修复 |
| --- | --- | --- |
| Linux 上 `error: linker not found` | 缺少 `gcc` / `build-essential` | `apt install build-essential pkg-config libssl-dev` |
| Linux 上 `failed to run custom build command for openssl-sys` | OpenSSL 头文件缺失 | `apt install libssl-dev` |
| 运行时 `avifenc: command not found` | `avifenc` 不在 `PATH` 且 `avifenc_path` 未设置 | 安装 libavif CLI 工具,或在配置中设置 `avifenc_path` |
| `该二进制未启用 sftp feature` | 用 `--no-default-features` 构建 | 用 `--features sftp` 重新构建 |
| S3 PUT 返回 403 SignatureDoesNotMatch | 自定义 endpoint 用了错误的 canonical URI 风格 | 签名器对自定义 endpoint 期望 path-style —— 检查 `s3.endpoint` 格式 |
| Release 中归档为空 | 矩阵某项失败 | 重跑 release workflow;查看失败 target 的任务日志 |