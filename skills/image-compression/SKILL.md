---
name: image-compression
description: 当 agent 需要非交互式运行 ImageCompression CLI 来扫描、整理、压缩、缩放或上传图片目录时使用；尤其适用于需要 JSON Lines 输出、批处理和避免混入本地测试产物的场景。
---

# ImageCompression

## 核心原则

`ImageCompression` 是 Rust TUI + CLI 图片批处理工具。agent 运行任务时只使用 CLI，不启动 TUI。

- 始终把 `--json` 放在子命令前，按 JSON Lines 解析 `start`、`progress`、`error`、`done` 事件。
- 输入和输出路径使用绝对路径；路径可包含中文、空格和方括号。
- 不硬编码开发者机器路径。优先读取 `$env:IMAGECOMPRESSION_BIN`，否则使用 `ImageCompression` 或 `ImageCompression.exe` 从 `PATH` 查找。
- 不把用户的本地目录名、测试相册名、临时输出目录写进 skill、文档、提交说明或发布说明；示例统一使用占位路径。

PowerShell 调用模板：

```powershell
$ICLI = $env:IMAGECOMPRESSION_BIN
if (-not $ICLI) { $ICLI = "ImageCompression" }

& $ICLI --json scan --input "D:\photos\raw"
```

## 写入边界

agent 只能写入用户明确指定的业务输出目录，例如 `--output`、`--prepared-output`、`--compressed-output` 对应的位置。没有明确要求时，不要写入仓库根目录、源码目录或用户原始输入目录。

严禁创建、写入、暂存、提交或上传这些本地/测试产物：

- `.claude/`、`.local/`、`local/`
- `build/`、`target/`
- `tmp/`、`temp/`、`.tmp/`
- `*_compressed/`、`test-output/`、`fixtures-output/`
- 本地样例图片目录、本地测试相册目录
- `.zip`、`.7z`、`.rar` 等本地压缩包
- 运行日志、临时配置、凭据文件

测试规则：

- 运行工具验证时，优先使用系统临时目录或明确的外部测试目录，验证后清理。
- 不要为了演示 skill 而新增或提交测试输入图片、测试输出目录、压缩结果目录。
- 只有在用户明确要求修改源码并需要回归保护时，才可以新增仓库内测试源码；测试源码要小而可复现，不能依赖本地图片包或私有目录。
- 提交前必须运行 `git status --short --ignored`，只暂存本次需要的源码、文档或 skill 文件。

上传规则：

- `upload` 只上传用户传给 `--input` 的目标目录。
- 不要把仓库根目录、`build/`、`target/`、`local/`、测试目录或压缩包当作上传输入。
- 上传路径由配置控制；如果配置没有自定义上传子路径，保持工具默认行为，不在 skill 中写死本地目录名。

## 子命令

| 子命令 | 用途 | 常用参数 |
|---|---|---|
| `scan` | 扫描目录并统计文件 | `--input`, `--recursive` |
| `prepare` | 整理、复制、重命名文件 | `--input`, `--output`, `--no-rename`, `--overwrite`, `--recursive` |
| `compress` | 压缩为 AVIF / WebP / JPEG | `--input`, `--output`, `--format`, `--quality`, `--min-quality`, `--speed`, `--workers`, `--avifenc`, `--overwrite`, `--recursive` |
| `upload` | 上传目录到 S3 / FTP / SFTP | `--input`, `--config`, `--recursive` |
| `all` | prepare -> compress -> 可选 upload | `--input`, `--prepared-output`, `--compressed-output`, `--format`, `--quality`, `--upload`, `--config` |
| `version` | 输出版本 | 无 |

`--json` 是全局参数，放在子命令前：

```powershell
& $ICLI --json compress --input "D:\photos\prepared" --output "D:\photos\compressed" --format avif
```

## 压缩和缩放

AVIF 依赖 `avifenc`。Windows Release 包会附带官方 libavif 的 `windows-artifacts\avifenc.exe`；源码 checkout 不应该提交这些 exe。本地开发需要时，从 AOMediaCodec/libavif release 解压到被忽略的本地目录，并通过配置或 `--avifenc <dir>` 指向目录。

缩放参数：

- `--resize-mode none|width|height|percent|long_edge|short_edge|fit|fill|exact`
- `--resize-value N`
- `--keep-aspect-ratio` 或 `--no-keep-aspect-ratio`

`--no-keep-aspect-ratio` 只影响 `width` 和 `height` 模式。`long_edge`、`short_edge`、`fit` 默认不放大小图；`fill` 会覆盖指定正方形后居中裁剪；`exact` 会强制输出正方形，可能拉伸。

示例：

```powershell
& $ICLI --json compress `
  --input "D:\photos\prepared" `
  --output "D:\photos\compressed" `
  --format avif `
  --quality 35 `
  --resize-mode long_edge `
  --resize-value 1920
```

## 标准工作流

先扫描：

```powershell
& $ICLI --json scan --input "D:\photos\raw" --recursive
```

整理后压缩：

```powershell
& $ICLI --json prepare `
  --input "D:\photos\raw" `
  --output "D:\photos\prepared" `
  --recursive

& $ICLI --json compress `
  --input "D:\photos\prepared" `
  --output "D:\photos\compressed" `
  --format avif `
  --quality 35
```

一条龙：

```powershell
& $ICLI --json all `
  --input "D:\photos\raw" `
  --prepared-output "D:\photos\prepared" `
  --compressed-output "D:\photos\compressed" `
  --format avif `
  --quality 35
```

上传：

```powershell
& $ICLI --json upload --input "D:\photos\compressed"
```

## JSON 和退出码

JSON Lines 示例：

```jsonc
{"event":"start","phase":"compress","total":45}
{"event":"progress","phase":"compress","current":1,"total":45,"file":"0001.jpg","speed":0.4}
{"event":"error","phase":"compress","current":2,"total":45,"file":"0002.jpg","error":"..."}
{"event":"done","phase":"compress","total":45,"compressed":43,"skipped":0,"failed":2,"originalSize":1234567,"compressedSize":654321,"savedPercent":47.0,"elapsed":12.3,"outputDir":"..."}
```

退出码：

- `0`：全部成功。
- `1`：部分失败，可以针对失败文件或目录重试。
- `2`：参数或用法错误，不要盲目重试，先修正命令。

## 提交前检查

修改 skill、文档或源码后，至少检查：

```powershell
git status --short --ignored
git diff --check
```

确认没有把本地目录、测试输入、测试输出、压缩产物、构建产物或凭据文件纳入提交。只在用户明确要求时才执行 `git add`、`git commit`、`git push`。
