---
name: image-compression
description: 用来调用本地 ImageCompression 工具（纯 Rust TUI + CLI，pikpaktui 风格重构）。当用户要求批量压缩图片、整理文件目录、上传到 S3/FTP/SFTP，或希望脚本化（非交互）运行这个工具时，使用本 skill。优先使用 CLI 模式给 agent。
---

# image-compression

`ImageCompression` 是仓库 `C:\Users\sakurajiamai\Desktop\code\ImageCompression` 下的**纯 Rust** TUI + CLI 工具（完全参考 pikpaktui 的样式、布局、代码组织与 agent 友好设计）。

构建后二进制位于：
- `build/bin/ImageCompression.exe`（推荐位置，agent/skill 默认使用此路径）
- 或直接使用 `cargo build --release` 产生的 `target/release/ImageCompression.exe`（需手动更新 skill 中的 ICLI 路径）

**二进制同时支持两种模式**：
- 不带任何参数 → 启动 ratatui TUI（Miller 三列布局 + 键盘导航，适合人类交互）
- 带子命令参数 → 进入 CLI，直接跑批处理并退出（**agent 强烈推荐使用此模式**）

**优先用 CLI 而不是 TUI。** TUI 适合人类操作，agent 跑批量任务时**必须**走 CLI，并加上 `--json` 把进度变成结构化事件流，便于解析。

## 专为 AI Agent 设计（OpenClaw、Hermes 等）

此 skill 专门为智能体（如 OpenClaw、Hermes）优化：
- 所有操作通过 CLI 子命令，非交互式。
- 始终使用 `--json` 输出结构化 JSON Lines，便于程序解析。
- 清晰退出码：0=完全成功，1=部分失败（可重试），2=参数/用法错误。
- 支持 dry-run 风格（通过 --json 观察计划）。
- 推荐 agent 在调用前确保 config.json 已由人类配置好凭据。
- 输入输出路径必须使用绝对路径，避免相对路径问题。
- 中文路径、空格、特殊字符均已测试支持。

**Agent 调用模板**（推荐在 skill 中定义 ICLI）：
```bash
ICLI="C:/Users/sakurajiamai/Desktop/code/ImageCompression/build/bin/ImageCompression.exe"
"$ICLI" --json <subcommand> [args...]
```

解析输出时使用 `jq` 或逐行 `json.loads` 处理事件流。

## 调用方法

```powershell
# 推荐设置变量
$ICLI = "C:/Users/sakurajiamai/Desktop/code/ImageCompression/build/bin/ImageCompression.exe"

# 或者直接使用 cargo 产物
# $ICLI = "C:/Users/sakurajiamai/Desktop/code/ImageCompression/target/release/ImageCompression.exe"

# 看帮助
& $ICLI --help
& $ICLI <子命令> --help

# 看版本
& $ICLI version
```

## 子命令一览

| 子命令 | 用途 | 关键参数 |
|---|---|---|
| `scan` | 扫描目录统计图片 / 视频 / 其他 | `--input`, `--recursive` |
| `prepare` | 重命名 + 整理文件到目标目录 | `--input`, `--output`, `--no-rename`, `--overwrite`, `--recursive` |
| `compress` | 批量压缩为 AVIF / WebP / JPEG | `--input`, `--output`, `--format`, `--quality`, `--min-quality`, `--speed`, `--workers`, `--avifenc`, `--overwrite`, `--recursive` |
| `upload` | 把目录里文件上传到 S3 / FTP / SFTP | `--input`, `--config`, `--recursive` |
| `all` | 准备 → 压缩 →(可选)上传 一条龙 | `--input`, `--prepared-output`, `--compressed-output`, `--format`, `--quality`, `--upload`, `--config` |
| `version` | 打印版本 | — |
| `help` | 打印总帮助 | — |

## 注意事项

- `upload` 读取 `~/.imagecompression/config.json`（可以用 `--config` 覆盖），不传任何协议参数。
- `compress` 走本地 `avifenc` 编码 AVIF，需要确保二进制在 `PATH` 或 `--avifenc <dir>` 指定；
  JPEG 用 Rust `image` crate 实现，WebP 走系统 `cwebp`。
- 中文路径、空格、方括号目录名都能正常处理（测试已覆盖）。
- TUI 支持 pikpaktui 式 Tab 补全、本地文件 Miller 预览（ratatui-image 或回退块/ASCII）。**agent 请始终使用 CLI + --json**。

## JSON 事件流（给 agent 解析）

加 `--json` 之后，每一行是一条 JSON，事件类型如下：

```jsonc
{"event":"start","phase":"compress","total":45}
{"event":"progress","phase":"compress","current":1,"total":45,"file":"0001.jpg","speed":0.4}
{"event":"error","phase":"compress","current":2,"total":45,"file":"0002.jpg","error":"..."}
{"event":"done","phase":"compress","total":45,"compressed":43,"skipped":0,"failed":2,
 "originalSize":1234567,"compressedSize":654321,"savedPercent":47.0,"elapsed":12.3,"outputDir":"..."}
```

非 `--json` 模式则是人类可读的行，例如：

```
[compress] 开始 共 45 个文件
[compress] 1/45  0001.jpg  0.4 张/秒
[upload] 1/45 OK 0001.jpg -> https://cdn.example.com/0001.avif
```

**推荐写法：agent 用 `jq` 或 `Select-String` 解析，而不是看 stderr。**

## 标准工作流

### 1. 单纯压缩

```powershell
& $ICLI --json compress `
  --input D:/photos/raw `
  --output D:/photos/compressed `
  --format avif `
  --quality 35
```

### 2. 整理 + 压缩（典型相册）

```powershell
& $ICLI --json prepare `
  --input D:/photos/raw `
  --output D:/photos/prepared

& $ICLI --json compress `
  --input D:/photos/prepared `
  --format avif --quality 35 --speed 6
```

### 3. 一条龙：整理 → 压缩 → 上传

```powershell
# 先确保 ~/.imagecompression/config.json 已经填好 S3/FTP/SFTP 凭据
& $ICLI --json all `
  --input D:/photos/raw `
  --format avif --quality 35 `
  --upload
```

### 4. 把大量图片上传到自定义远程子路径

在 `~/.imagecompression/config.json` 的 `upload.custom_path` 字段填好，例如 `artist/album`，然后：

```powershell
& $ICLI --json upload --input D:/photos/compressed
```

`EffectiveConfig` 会把 `custom_path` 拼到协议基础路径上（S3 Prefix / FTP RemoteDir / SFTP RemoteDir）。

## 专为 OpenClaw / Hermes 等智能体优化的调用注意

1. **始终加 `--json`**（放在子命令前）。输出为 JSON Lines，agent 必须逐行解析事件（start/progress/error/done）。
   - 示例解析（Python）：
     ```python
     import json, subprocess
     proc = subprocess.Popen([ICLI, "--json", "compress", ...], stdout=subprocess.PIPE)
     for line in proc.stdout:
         event = json.loads(line)
         if event["event"] == "done":
             print(event["savedPercent"])
     ```
   - 使用 `jq` 过滤： ` | jq 'select(.event=="done") | .savedPercent' `

2. **不要自己写 `if (avifenc exists)` 检测**。直接用 `--avifenc <dir>` 或让二进制从 PATH 找（推荐在 skill 中硬编码常见路径）。

3. **退出码严格处理**：
   - 0 = 全部成功
   - 1 = 部分文件失败（可重试该目录，或跳过失败文件）
   - 2 = 参数错误 / 用法错误（不要重试，检查 prompt）

4. **大目录压缩建议**：avif 强制单线程（内部已处理），其他格式可用 `--workers 4` 加速。

5. **凭据管理**：**永远不要让 agent 修改 `~/.imagecompression/config.json`**。凭据由人类提前在 TUI 或手动配置好。agent 调用前可读取 config 验证（但不写）。

6. **错误处理**：S3 401/403 通常是 key 错误或空格污染，提示人类重新配置。其他网络错误可重试。

7. **路径要求**：input/output 必须绝对路径。Windows 用 `/` 或 `\\` 均可，二进制已处理。

8. **干运行风格**：可先用 `scan` 获取文件数，再决定是否执行 prepare/compress。compress 支持 overwrite/rename 策略。

## 完整路径

| 用途 | 路径 |
|---|---|
| 可执行二进制 | `C:\Users\sakurajiamai\Desktop\code\ImageCompression\build\bin\ImageCompression.exe` |
| 配置文件 | `C:\Users\sakurajiamai\.imagecompression\config.json` |
| avifenc 工具目录 | 默认 `build/bin/windows-artifacts/avifenc.exe`，可在配置 `avifenc_path` 改 |
| 工作目录 | 任意；CLI 参数都是绝对路径 |

## 验证清单（调完一次后跑一遍）

- [ ] `ImageCompression version` 返回 `0.2.0`（或当前 Cargo 版本）
- [ ] `ImageCompression scan --input <dir>` 打印图片/视频数量
- [ ] `ImageCompression --json prepare --input <dir>` 产生 start/progress/done JSON 事件
- [ ] `ImageCompression --json compress --input <dir> --format jpeg` 每行一个 JSON，包含 savedPercent/elapsed
- [ ] `ImageCompression`（无参数）能正常启动 TUI（可选，agent 主要验证 CLI）
- [ ] 配置文件兼容：`~/.imagecompression/config.json` 可直接加载（proxy legacy、avifenc_path normalize 等行为一致）
- [ ] 中文目录 + 括号路径正常（prepare 重命名 0001.jpg / video001.mp4 规则一致）

构建命令（在项目根目录执行）：
```powershell
cargo build --release
mkdir -p build/bin
Copy-Item target/release/ImageCompression.exe build/bin/ImageCompression.exe -Force
```

**推荐方式**：直接从 GitHub Releases 下载预构建二进制（多平台 .zip / .tar.gz + sha256sums.txt），无需本地编译 Rust。

推送 `git tag vX.Y.Z && git push --tags` 即可触发 GitHub Actions 自动构建并发布所有平台产物（类似 pikpaktui）。

如果以上任何一项失败，先确认 `cargo build --release` 成功，然后把 exe 放到 build/bin 位置。