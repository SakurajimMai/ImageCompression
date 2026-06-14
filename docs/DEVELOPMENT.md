# 开发指南

搭建可用的开发环境、运行测试,以及编写符合项目规范的代码。

## 前置依赖

- **Rust** —— 最新 stable。通过 [rustup](https://rustup.rs/) 安装。
- **avifenc** —— 安装 libavif 命令行工具。Linux:`apt install libavif-bin`
  (或从源码编译)。macOS:`brew install libavif`。Windows:从
  [AOMediaCodec/libavif](https://github.com/AOMediaCodec/libavif/releases)
  下载 `windows-artifacts.zip`,把内容放入 `PATH` 即可。
- **cwebp** —— 安装 webp 工具。Linux:`apt install webp`。macOS:
  `brew install webp`。Windows:从
  [libwebp releases](https://storage.googleapis.com/downloads.webmproject.org/releases/webp/index.html)
  下载。
- **OpenSSL 开发头文件**(Linux/macOS 上启用默认 `sftp` feature 时才需要)。
  Linux:`apt install pkg-config libssl-dev zlib1g-dev`。macOS:
  `brew install pkg-config openssl zlib`。**Windows** 使用默认 MSVC 工具链
  时无需额外配置;如果需要 vendored OpenSSL,用
  `--features sftp-vendored-openssl`。

## 克隆与构建

```bash
git clone https://github.com/SakurajimMai/ImageCompression.git
cd ImageCompression
cargo build --release
```

Release profile(`Cargo.toml:46`)已调优:LTO、`opt-level = "s"`、
`codegen-units = 1`、`strip = true`、`panic = "abort"`。

Windows 上二进制名是 `ImageCompression.exe`;Unix 上是 `ImageCompression`
(`[[bin]]` 名保留;发布流水线在归档时统一改成小写 `imagecompression`)。

## 项目结构(开发者视角)

```
src/
├── main.rs          # argv 分发,文件很小
├── config.rs        # Config 结构 + load/save + ProxyConfig.normalize
├── theme.rs         # emoji 图标(只有一个函数)
├── cmd/             # CLI 子命令,每个命令一个文件
├── core/            # 纯领域逻辑,无 I/O 框架
│   ├── mod.rs       # 模块导出 + 测试挂载
│   ├── scanner.rs
│   ├── prepare.rs
│   ├── compress.rs  # 调度器 + 编码器
│   ├── upload.rs    # trait + S3 / FTP / SFTP 实现 + SigV4 + 代理
│   └── workflow.rs  # 串联流水线辅助
└── tui/             # ratatui 界面
    └── mod.rs       # App、run()、draw()、handle_key()

skills/image-compression/SKILL.md  # agent 面向的使用说明
.github/workflows/                 # CI + 发布流水线
docs/                              # 本文档
```

## 日常命令

```bash
# 对所有 target 做类型检查(比完整构建快)
cargo check --all-targets

# 运行完整测试套件
cargo test --all

# 格式与 lint 关卡
cargo fmt -- --check
cargo clippy --all-targets -- -D warnings

# 构建 release
cargo build --release

# 端到端冒烟测试 CLI 子命令
./target/release/ImageCompression version
./target/release/ImageCompression scan --input ./tests/fixtures --json
./target/release/ImageCompression prepare --input ./tests/fixtures --output ./tmp/prep --json
./target/release/ImageCompression --json compress --input ./tmp/prep --format jpeg --quality 80
./target/release/ImageCompression --json all --input ./tmp/prep --format jpeg --quality 80
```

## 测试

当前测试刻意做得窄 —— 它们锁定的是"代码上不直观、容易回归"的行为:

| 文件 | 覆盖 |
| --- | --- |
| `src/config_test.rs` | `default_config()` + `normalize()`;旧版 `ProxyConfig.url` 解析 |
| `src/core/compress_tests.rs` | 当输入目录不存在时 `compress_directory` 报错(递归与非递归) |
| `src/core/upload_tests.rs` | 当输入目录不存在时 `collect_files` 报错;自定义 endpoint 与 AWS virtual-host 的 `canonical_uri_for_s3_put`;`FtpUploader::proxy_url()`;`S3Uploader::canonical_uri_for_key` |

新增行为时,**先写失败测试**。现有测试遵循以下模式:

```rust
#[test]
fn compress_directory_returns_error_for_missing_recursive_input() {
    let dir = tempfile::tempdir().unwrap();
    let missing = dir.path().join("missing");
    let opts = minimal_options(missing.to_string_lossy().to_string(), true);

    let err = compress_directory(Arc::new(()), opts, None, None).unwrap_err();

    assert!(
        err.to_string().contains("missing"),
        "unexpected error: {err:#}"
    );
}
```

注意:

- `tempfile::tempdir()` 让测试自包含。
- `compress_directory` 上的 `Runner` 回调是测试编码器调用的接缝 —— 不必真
  启动 `avifenc` / `cwebp`。

## 编码规范

本项目遵循根目录 `CLAUDE.md` 中记录的规则:

- **单一职责** —— 每个模块与函数只做一件事。
- **组合优于继承** —— 注意 `Uploader` trait(`src/core/upload.rs:54`)。
- **接口优于单例** —— 进度回调与 runner 都显式传入。
- **显式优于隐式** —— 没有隐藏全局状态。
- **合理范围内 TDD** —— 永远不要跳过或 `.unwrap()` 吞掉测试。
- **尽早报错并带上下文** —— 每个可能失败的调用都使用 `?`、`with_context`
  或 `anyhow!`,并附上足够定位的信息。
- **匹配周边代码的密度** —— 短函数保持紧凑,长函数用顶部注释说明 *为何*
  存在。

### 子命令风格

CLI 子命令简短、手写,共享同一个 `match args[i].as_str()` 循环。结构保持
一致:

```rust
pub fn run(args: &[String]) -> Result<()> {
    let mut input = String::new();
    // ...声明每个 flag 的局部变量...
    let mut json = false;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--input"   => { i += 1; input = args.get(i).cloned().unwrap_or_default(); }
            "--json"    => json = true,
            "-h" | "--help" => return crate::cmd::print_command_help("compress"),
            _ => {}
        }
        i += 1;
    }

    if input.is_empty() { return Err(anyhow::anyhow!("--input 必填")); }
    // ...业务逻辑...
}
```

新增 flag 时:

1. 在 `run` 顶部添加局部变量。
2. 在解析循环中添加 `match` 分支。
3. 在函数其余部分使用该变量。
4. 把 flag 加进 `src/cmd/mod.rs::command_help_text` 的帮助字符串。

### 输出风格

两种输出模式:

- **人类**模式(默认)—— 使用 `src/cmd/mod.rs` 中共享的 `B`、`D`、`G`、`R`
  ANSI 助手渲染彩色文本。
- **JSON** 模式(传 `--json`)—— JSON Lines,每行一条事件,可被 `jq` 或任何
  JSON 解析器消费。形状在 [API.md](./API.md) 中说明。

流式进度的子命令应始终先发一行 `{"event":"start", …}`,最后发一行
`{"event":"done", …}`,以便消费者能括起一次运行。

### Commit 风格

Commit 信息遵循项目现有节奏:

```
<type>: <祈使句摘要>

<可选正文,说明为什么>
```

历史中出现的 `type`:feat、fix、chore、docs、refactor。每个 commit 必须:

1. 能编译(`cargo check --all-targets`)。
2. 通过所有测试(`cargo test --all`)。
3. 只涉及一个逻辑关注点。

## 调试技巧

- 项目未配置 `RUST_LOG=debug` —— 故意没有日志依赖。调查时用 `eprintln!`
  临时调试,然后删除。
- `--json` 是跟踪 CLI 子命令行为最友好的方式。管道给 `jq` 实时观察:

  ```bash
  ./ImageCompression --json compress --input ./photos --format avif --quality 35 \
    | jq -c 'select(.event=="progress") | {file: .currentFile, speed}'
  ```

- `tempfile::tempdir()` 让测试创建临时目录,不污染工作树。
- `compress_directory` / `upload_directory` 上的 `Runner` 与 `ProgressFunc`
  回调是不实际启动子进程而进行单元测试的最干净的接缝。

## 本地 AVIF/WebP 测试

项目假设 `avifenc` 与 `cwebp` 在 `PATH` 上。要覆盖:

```bash
# 告诉二进制在哪里找 avifenc
./ImageCompression --json compress --input ./photos --avifenc /opt/libavif/bin
```

或在 `~/.imagecompression/config.json` 中:

```json
{
  "avifenc_path": "build/bin/windows-artifacts"
}
```

`avifenc_path` 会被归一化:可执行文件名(`avifenc.exe`)折叠为空(依赖
`PATH`);目录原样保留;以 `avifenc.exe` 结尾的完整路径会被改写为父目录。
参见 `normalize_avifenc_path`(`src/config.rs:262`)。

## 常见陷阱

- **Linux 上忘记启用 SFTP feature** → 运行时错误 *"该二进制未启用 sftp
  feature"*。用 `--features sftp` 或 `--features sftp-vendored-openssl`
  重新构建。
- **自定义 S3 endpoint 路径风格错** → 403 SignatureDoesNotMatch。签名器
  对自定义 endpoint 期望 path-style,即 `/{bucket}/{key}`;AWS 用 virtual-host
  风格。`canonical_uri_for_s3_put`(`src/core/upload.rs:463`)展示了两种
  形式。
- **AVIF worker 争用** → 不要为 AVIF 提高 `workers`,模块内部已经把它固定
  为 1。
- **配置文件缺失** → `load()` 返回默认值,你**不会**得到错误。通过 TUI 的
  `,` overlay 或手动编辑写入任何修改。