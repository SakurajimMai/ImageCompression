# API 与 CLI 参考

本文档描述 ImageCompression 的用户面:CLI 子命令、配置文件,以及 AI Agent
使用的 JSON 事件协议。

## 调用

```text
ImageCompression                       # 启动 TUI(无参数)
ImageCompression [options] <command>   # CLI 模式
ImageCompression version               # 打印版本
ImageCompression help                  # 顶层帮助
ImageCompression <command> --help      # 命令级帮助
```

二进制由 `src/main.rs` 构建,Windows 名为 `ImageCompression.exe`,Unix
名为 `ImageCompression`。发布流水线在归档时把 Unix 二进制统一改为小写
`imagecompression`。

## 全局选项

| 标志 | 效果 |
| --- | --- |
| `--help` / `-h` | 打印帮助。带子命令时,打印该子命令的帮助。 |
| `--version` / `-V` / `version` | 打印 `imagecompression <version>`。 |

## 子命令

| 命令 | 概要 | 关键标志 |
| --- | --- | --- |
| `scan` | 遍历目录,统计图片 / 视频 / 其他数量。 | `--input`、`--recursive`、`--no-recursive`、`--json` |
| `prepare` | 重命名并复制文件到组织好的输出树。 | `--input`、`--output`、`--no-rename`、`--overwrite`、`--recursive`、`--json` |
| `compress` | 把所有图片压缩为 AVIF / WebP / JPEG。 | `--input`、`--output`、`--format`、`--quality`、`--min-quality`、`--speed`、`--resize-mode`、`--resize-value`、`--workers`、`--avifenc`、`--overwrite`、`--json` |
| `upload` | 把目录中的文件上传到 S3 / FTP / SFTP。 | `--input`、`--config`、`--recursive`、`--json` |
| `all` | 一条龙:scan → prepare → compress →(可选)upload。 | `--input`、`--prepared-output`、`--compressed-output`、`--format`、`--quality`、`--resize-mode`、`--resize-value`、`--upload`、`--config`、`--json` |

退出码:

| 代码 | 含义 |
| --- | --- |
| `0` | 所有文件成功。 |
| `1` | 至少一个文件失败(compress / upload / all)。 |
| `2`(经由 `anyhow`) | 参数或用法错误。 |

### `scan`

```bash
ImageCompression scan --input ./photos [--recursive] [--json]
```

输出(非 JSON):

```
目录: ./photos
图片: 12
视频: 3
其他: 0
子目录: 4
总体积: 123456 bytes
```

JSON 输出(`--json`)是单个 `ScanResult` 对象:

```json
{
  "baseDir": "./photos",
  "images": ["./photos/0001.jpg", "..."],
  "videos": [],
  "others": [],
  "totalSize": 123456,
  "subdirs": 4
}
```

### `prepare`

```bash
ImageCompression prepare --input ./raw --output ./prepared [--no-rename] [--overwrite] [--json]
```

行为:

- 读取目录树,按父目录分组,把图片重命名为 `0001.jpg`(4 位补零),视频
  重命名为 `video001.mp4`。若指定 `--no-rename`,保留原始文件名。
- 把相对子目录布局镜像到 `--output`。未指定输出时,默认是 `<input>_prepared`。
- 未传 `--overwrite` 时,拒绝覆盖已存在目标,并显式报错。

`--json` 时输出的事件:

```jsonc
{"event":"start","phase":"prepare","total":45}
{"event":"done","phase":"prepare","outputDir":"./prepared","totalFiles":45}
```

### `compress`

```bash
ImageCompression compress --input ./prepared --output ./out \
    --format avif --quality 35 --speed 6 --min-quality 20 \
    [--resize-mode long_edge --resize-value 1920] \
    [--workers N] [--avifenc /opt/libavif/bin] [--overwrite] [--json]
```

行为:

- `--format` 选择编码器:
  - `avif` —— 调用 `avifenc`(推荐,输出最小)。
  - `webp` —— 调用 `cwebp`。
  - `jpeg` —— 纯 Rust `image::codecs::jpeg::JpegEncoder`。
- `--quality` 由各编码器解释:JPEG/WebP 用作 `-q`,AVIF 用作 `--max`
  (除非给了 `--min-quality`,否则 `--min = quality - 15`)。
- `--speed` 映射到 `avifenc --speed`(0–10,数值越小越慢、越小)。
- AVIF 时 `--workers` 被忽略(内部强制为 1,因为 `avifenc` 自身已并行);
  WebP/JPEG 接受该参数。
- 缩放可以直接用 CLI 参数启用:
  `--resize-mode <mode> --resize-value <n>`。`width` / `height` 默认保持
  长宽比,可用 `--no-keep-aspect-ratio` 关闭。
- 冲突策略:
  - `--overwrite` → 覆盖已有输出。
  - 默认 → 重命名为 `0001_1.jpg`、`0001_2.jpg` …。

JSON 事件:

```jsonc
{"event":"start","phase":"compress","total":45}
{"event":"progress","phase":"compress","current":1,"total":45,"file":"0001.jpg","speed":0.4,...}
{"event":"error","phase":"compress","current":2,"total":45,"file":"0002.jpg","error":"..."}
{"event":"done","phase":"compress","total":45,"compressed":43,"skipped":0,"failed":2,
 "originalSize":1234567,"compressedSize":654321,"savedPercent":47.0,"elapsed":12.3,"outputDir":"..."}
```

### 缩放模式

可以通过 CLI 的 `--resize-mode` + `--resize-value` 传入,也可以在
`config.json` 的 `compress.resize_mode` + `compress.resize_value` 中配置
供 TUI 使用。模式逻辑在 `resize_image`(`src/core/compress.rs:242`)中实现:

| 模式 | 行为 |
| --- | --- |
| `none` | 不缩放(默认)。 |
| `width` | 把宽度调整为 `resize_value`;若 `keep_aspect_ratio`,高度按比例。 |
| `height` | 把高度调整为 `resize_value`。 |
| `percent` | 两个维度乘以 `resize_value / 100`。 |
| `long_edge` | 长边变成 `resize_value`;另一边按比例。 |
| `short_edge` | 短边变成 `resize_value`。 |
| `fit` | 让图片**容纳**于 `value × value` 框内。 |
| `fill` | 缩放到覆盖 `value × value` 框,然后裁剪中心。 |
| `exact` | 强制恰好 `value × value`(忽略长宽比)。 |

### `upload`

```bash
ImageCompression upload --input ./compressed [--config /path/to/config.json] [--json]
```

读取 `~/.imagecompression/config.json`(或 `--config <path>`),通过
`effective_config`(`src/core/upload.rs:99`)解析有效远程目标,然后上传
`--input` 中每个文件:

- **S3** —— SigV4 PUT。若 `s3.endpoint` 为空,使用 AWS virtual-host 风格
  (`<bucket>.s3.amazonaws.com/<key>`);否则使用 path-style
  (`<endpoint>/<bucket>/<key>`)。`s3.domain` 覆盖响应中的公网 URL 前缀;
  否则返回 PUT URL。
- **FTP** —— 连接(可走代理 dialer)、登录、创建远程目录,然后 `put_file`
  每个对象。
- **SFTP** —— 需要 `sftp` cargo feature;否则返回 `UnsupportedUploader`
  中的 "未启用 sftp feature" 错误。

若配置中设置了 `upload.custom_path`,流水线会把它作为后缀拼到协议的基础
路径(S3 prefix、FTP `remote_dir`、SFTP `remote_dir`)。否则用源目录名
作为 prefix / remote_dir。

JSON 事件:

```jsonc
{"event":"start","phase":"upload","total":45}
{"event":"progress","phase":"upload","current":1,"total":45,"file":"0001.jpg","url":"https://cdn/.../0001.avif"}
{"event":"error","phase":"upload","current":2,"total":45,"file":"0002.jpg","error":"..."}
{"event":"done","phase":"upload","total":45,"uploaded":43,"failed":2,"urls":[...],"errors":[...]}
```

### `all`

```bash
ImageCompression all --input ./raw --format avif --quality 35 \
    [--resize-mode long_edge --resize-value 1920] \
    [--upload] [--config ...] [--json]
```

一条龙工作流:

1. `scan_directory(input)`。
2. `prepare::plan_operations` + `prepare::execute_operations` →
   `<input>_prepared`(或 `--prepared-output`)。
3. `compress::compress_directory` → `<prepared>_compressed`(或
   `--compressed-output`)。
4. 若 `--upload`,使用配置执行 `upload::upload_directory`。

`all` 的缩放参数会原样转发给压缩阶段。

省略 `--upload` 时,无失败返回 `0`,压缩有失败返回 `1`。带 `--upload` 时,
任一阶段失败均返回 `1`。

## JSON 事件协议

每个流式工作的 CLI 子命令在 `--json` 下向 stdout 发送 JSON Lines。形状是
稳定的;可加新字段,但既有字段在废弃周期内不会被改名或删除。

### `scan`

单个对象:

```jsonc
{
  "baseDir": "./photos",
  "images": ["..."],
  "videos": ["..."],
  "others": ["..."],
  "totalSize": 123456,
  "subdirs": 4
}
```

### `prepare` / `compress` / `upload` / `all`

一个括号序列:

```jsonc
{"event":"start",   "phase":"<phase>", "total":N}
{ <一条或多条 progress/error 对象> }
{"event":"done",    "phase":"<phase>", "...":"..."}
```

事件形状:

| 阶段 | `start` 字段 | `done` 字段 |
| --- | --- | --- |
| `prepare` | `total` | `outputDir`、`totalFiles` |
| `compress` | `total` | `total`、`compressed`、`skipped`、`failed`、`originalSize`、`compressedSize`、`savedPercent`、`elapsed`、`outputDir` |
| `upload` | `total` | `total`、`uploaded`、`failed`、`urls`、`errors` |

进度事件共享基础形状,按阶段填充可选字段(compress 加 `currentFile`、
`compressedSize`、`compressed`、`skipped`、`failed`、`speed`、`elapsedSec`;
upload 加 `sourceDir`、`url`;prepare 每个文件发一行 progress)。

## TUI 按键绑定

| 键 | 动作 |
| --- | --- |
| `j` / `↓` | 下移选中 |
| `k` / `↑` | 上移选中 |
| `Enter` | 进入目录 / 确认操作 |
| `Backspace` | 返回上级目录 |
| `r` | 扫描当前目录(后台线程) |
| `p` | 整理(后台线程;需要已有扫描结果) |
| `c` | 压缩(后台线程;使用已加载配置) |
| `,` | 打开 Settings overlay |
| `h` | 切换 Help overlay |
| `q` | 退出(带确认 overlay) |

在 Settings overlay 中(`src/tui/mod.rs:555`):

| 键 | 动作 |
| --- | --- |
| `j` / `↓` | 下一项设置 |
| `k` / `↑` | 上一项设置 |
| `Space` / `Enter` | 切换当前设置 |
| `s` | 保存到 `~/.imagecompression/config.json` |
| `Esc` | 取消并返回 Normal 模式 |

## 配置文件

路径:`~/.imagecompression/config.json`(Windows:
`%USERPROFILE%\.imagecompression\config.json`)。

文件用 `serde_json` 加载。缺失文件 → 默认值。无法解析的 JSON → 默认值
(不报错)。保存时会先归一化,所以文件始终可被新版 Rust 与旧 Go 构建共同
读取(仅限于旧 Go 能识别的字段)。

```json
{
  "last_input_dir": "",
  "last_output_dir": "",
  "prepare": {
    "rename_images": true,
    "rename_videos": true,
    "strip_exif": true,
    "output_mode": "new_directory"
  },
  "compress": {
    "format": "avif",
    "avif": {
      "min_quality": 20,
      "max_quality": 40,
      "speed": 6,
      "threads": "all",
      "yuv": "420",
      "depth": 8,
      "alpha_enabled": false,
      "alpha_min": 20,
      "alpha_max": 40,
      "lossless": false,
      "progressive": false
    },
    "webp_jpeg": { "quality": 80, "lossless": false },
    "skip_videos": true,
    "resize_mode": "none",
    "resize_value": 0,
    "keep_aspect_ratio": true,
    "workers": 1,
    "conflict_strategy": "rename"
  },
  "upload": {
    "protocol": "s3",
    "s3": {
      "endpoint": "",
      "bucket": "",
      "access_key": "",
      "secret_key": "",
      "region": "",
      "prefix": "",
      "domain": "",
      "proxy_url": ""
    },
    "ftp": {
      "host": "", "port": 21, "username": "", "password": "",
      "remote_dir": "/", "base_url": ""
    },
    "sftp": {
      "host": "", "port": 22, "username": "", "password": "",
      "key_path": "", "remote_dir": "/", "base_url": "", "domain_root": ""
    },
    "proxy": {
      "enabled": false,
      "url": "socks5://127.0.0.1:7890",
      "type": "socks5",
      "host": "127.0.0.1",
      "port": 7890,
      "username": "",
      "password": ""
    },
    "custom_path": ""
  },
  "avifenc_path": "",
  "language": "zh",
  "theme": "light"
}
```

### 代理优先级

`ProxyConfig::normalize()`(`src/config.rs:284`)是唯一裁决者:

- 仅当结构化字段处于默认值时,旧版 `url` 字段才会被解析并用于填充结构化
  字段。一旦你用结构化字段保存了配置,`url` 就只是旧保存的残留。
- `effective_url()`(`src/config.rs:322`)用结构化字段重建 URL;SOCKS5 /
  HTTP-CONNECT 实际消费的正是这个 URL。

## 配方:典型 agent 工作流

### 仅压缩

```bash
ICLI=./ImageCompression
"$ICLI" --json compress --input /abs/path/raw --output /abs/path/out \
  --format avif --quality 35 --speed 6
```

### 完整流水线

```bash
"$ICLI" --json all --input /abs/path/raw --format avif --quality 35 --upload
```

### 用 `jq` 流式查看进度

```bash
"$ICLI" --json compress --input /abs/path/raw --format avif \
  | jq -c 'select(.event=="progress") | {file: .currentFile, speed}'
```

### 把所有上传 URL 保存到日志

```bash
"$ICLI" --json upload --input /abs/path/out \
  | jq -r 'select(.url != null) | .url' > uploaded.txt
```
