# 用户使用指南

本指南面向**最终使用者**:摄影爱好者、图集整理者、运维人员。读完本指南
你应能独立完成"扫描 → 整理 → 压缩 → 上传"的完整流程,不必阅读源码。

> 如果你是开发者,请阅读 [DEVELOPMENT.md](./DEVELOPMENT.md) 和
> [ARCHITECTURE.md](./ARCHITECTURE.md)。

---

## 目录

1. [这是什么样的工具](#这是什么样的工具)
2. [安装](#安装)
3. [第一次运行](#第一次运行)
4. [理解配置文件](#理解配置文件)
5. [交互模式(TUI)](#交互模式tui)
6. [命令行模式(CLI)](#命令行模式cli)
7. [典型场景](#典型场景)
8. [进阶技巧](#进阶技巧)
9. [常见问题 FAQ](#常见问题-faq)
10. [故障排查](#故障排查)

---

## 这是什么样的工具

ImageCompression 是一个**单文件可执行程序**,帮你自动化以下繁琐流程:

```text
一堆散乱的图片
  → 扫描归类(图片/视频/其他)
  → 重命名整理(0001.jpg, video001.mp4 ...)
  → 批量压缩(AVIF / WebP / JPEG)
  → 上传到云存储(S3 / FTP / SFTP)
```

它支持两种使用方式:

| 模式 | 适合谁 | 特点 |
| --- | --- | --- |
| **TUI**(交互式终端界面) | 人工操作 | Miller 三列布局,键盘驱动,所见即所得 |
| **CLI**(命令行) | 脚本/Agent | 无交互,适合批处理,可输出 JSON 供程序解析 |

两种模式用的是同一份配置,行为完全一致 —— 你在 TUI 里调好的参数,跑
CLI 时会自动套用。

---

## 安装

### 方式一:下载预编译二进制(推荐)

从项目的 **GitHub Releases** 页面下载对应平台的归档:

| 平台 | 文件 |
| --- | --- |
| Windows x86_64 | `imagecompression-x86_64-windows.zip` |
| Windows ARM64 | `imagecompression-aarch64-windows.zip` |
| Linux x86_64 | `imagecompression-x86_64-linux.tar.gz` |
| Linux ARM64 | `imagecompression-aarch64-linux.tar.gz` |
| macOS Intel | `imagecompression-x86_64-macos.tar.gz` |
| macOS Apple Silicon | `imagecompression-aarch64-macos.tar.gz` |

每个归档里都有 `sha256sums.txt`,可以用 `sha256sum -c` 校验完整性。

解压后:

- **Windows**:得到 `ImageCompression.exe`(Windows 归档还会带
  `windows-artifacts/avifenc.exe` 等 AVIF 工具)。
- **Linux / macOS**:得到 `imagecompression` 可执行文件(macOS 首次运行
  可能需要在"系统设置 → 隐私与安全性"中允许)。

把可执行文件放到你喜欢的位置即可,无需安装。例如:

```bash
# Linux / macOS
mkdir -p ~/bin
mv imagecompression ~/bin/
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
```

### 方式二:从源码编译

如果你想用最新代码或平台没有预编译包:

```bash
git clone https://github.com/SakurajimMai/ImageCompression.git
cd ImageCompression
cargo build --release
```

Windows 产物在 `target/release/ImageCompression.exe`,Linux/macOS 在
`target/release/ImageCompression`。

### 安装外部编码器

为了让 AVIF 和 WebP 真正能压缩,你还需要系统里能找到 `avifenc` 与
`cwebp`:

| 工具 | Linux | macOS | Windows |
| --- | --- | --- | --- |
| `avifenc` | `apt install libavif-bin` 或 [官方 release](https://github.com/AOMediaCodec/libavif/releases) | `brew install libavif` 或 [官方 release](https://github.com/AOMediaCodec/libavif/releases) | 用预编译包里附带的 `windows-artifacts/avifenc.exe` |
| `cwebp` | `apt install webp` | `brew install webp` | [libwebp release](https://storage.googleapis.com/downloads.webmproject.org/releases/webp/index.html) |

如果 `avifenc` 不在 `PATH` 但你能告诉程序它在哪里也行 —— 见
[配置文件 → avifenc_path](#avifenc_path-avif-工具位置)。

**JPEG 压缩不需要任何外部工具**,纯 Rust 内置实现。

---

## 第一次运行

### 1. 启动 TUI

直接运行可执行文件(不带任何参数):

- **Windows**:双击 `ImageCompression.exe`,或在 PowerShell 中执行
  `.\ImageCompression.exe`。
- **Linux / macOS**:在终端运行 `./imagecompression`。

你会看到一个三列界面:

```
┌─ Parent ──┐ ┌─ Current dir ────────────┐ ┌─ Preview & Status ──────┐
│ ↑ Parent  │ │ 📁 sub_a                 │ │ Preview & Status        │
│ /photos   │ │ 📁 sub_b                 │ │ 📷 12  🎞 3            │
│           │ │ 🖼️ 001.jpg   (selected)  │ │ volume: 12345 bytes     │
│ (Backspace│ │ 🖼️ 002.jpg               │ │                         │
│  返回)    │ │                           │ │ last status: 欢迎使用…  │
└───────────┘ └───────────────────────────┘ │                         │
                                           │ 快捷键: j/k ↑↓ …        │
                                           └─────────────────────────┘
```

第一次启动时配置还是内置默认,先用 `,` 打开设置,把必要的字段填好
(详见下一节),然后 `s` 保存。

### 2. 试一下扫描

按 `r` 扫描当前目录。底部状态栏会显示"正在扫描...",完成后右侧会列出
图片/视频数量与总体积。

### 3. 试一下压缩

按 `c` 触发压缩。程序会在后台线程跑,你仍然可以用 `j/k` 浏览目录、查看
状态。完成后底部会显示"压缩完成:N 成功 / M 失败,节省 X%"。

---

## 理解配置文件

配置文件位于:

- **Windows**:`%USERPROFILE%\.imagecompression\config.json`
- **Linux / macOS**:`~/.imagecompression/config.json`

完整 schema 见 [API.md → 配置文件](./API.md#配置文件)。下面解释最常用
的几个字段。

### `compress.format`

输出格式,可以是 `avif`、`webp`、`jpeg`。

- **AVIF**:压缩率最高(同等画质下文件最小),编码最慢。
- **WebP**:压缩率中等,编码快,兼容性比 AVIF 略好。
- **JPEG**:兼容性最好,所有设备和浏览器都能看,文件最大。

### `compress.avif.*`

AVIF 编码参数。

```json
{
  "compress": {
    "format": "avif",
    "avif": {
      "min_quality": 20,
      "max_quality": 40,
      "speed": 6,
      "yuv": "420",
      "depth": 8
    }
  }
}
```

| 字段 | 含义 | 推荐值 |
| --- | --- | --- |
| `min_quality` / `max_quality` | 质量区间(0–63,越小越小) | `20` / `40`(默认) |
| `speed` | 编码速度(0–10,越小越慢越小) | `6`(平衡) |
| `yuv` | 色度子采样,`420`/`422`/`444` | `420` |
| `depth` | 位深,8 或 10 | `8` |

### `compress.webp_jpeg.quality`

WebP / JPEG 的质量(0–100,越大越接近原图)。默认 `80`,通常够用。

### `compress.resize_mode` + `compress.resize_value`

缩放规则。把所有图片统一到某个尺寸。详见 [API.md → 缩放模式](./API.md#缩放模式)。

| 场景 | 推荐设置 |
| --- | --- |
| 不缩放(默认) | `resize_mode: "none"` |
| 缩到最长边 1920 | `resize_mode: "long_edge"`,`resize_value: 1920` |
| 缩到宽度 1280,高度按比例 | `resize_mode: "width"`,`resize_value: 1280` |
| 缩到 50% | `resize_mode: "percent"`,`resize_value: 50` |

### `compress.conflict_strategy`

目标目录已有同名文件时怎么办:

- `rename`(默认):改成 `0001_1.jpg`、`0001_2.jpg`,**不覆盖**。
- `overwrite`:直接覆盖。
- `skip`:跳过该文件。

### `avifenc_path`(AVIF 工具位置)

如果 `avifenc` 不在系统 `PATH`,可以在这里指定目录或可执行文件路径:

```json
{
  "avifenc_path": "C:/Users/YourName/AppData/Local/Programs/avif-tools"
}
```

程序会自动识别以下形式:

- `"avifenc"` / `"avifenc.exe"` → 视为空(走 `PATH`)
- `"/some/dir"` → 在该目录里找 `avifenc` / `avifenc.exe`
- `"/some/dir/avifenc.exe"` → 自动截取到目录

### `upload.protocol`

上传协议,可以是 `s3`、`ftp`、`sftp`。

### `upload.s3.*`(S3 / R2 / MinIO 等 S3 兼容存储)

```json
{
  "upload": {
    "protocol": "s3",
    "s3": {
      "endpoint": "https://s3.amazonaws.com",
      "bucket": "my-photo-bucket",
      "access_key": "AKIA...",
      "secret_key": "...",
      "region": "us-east-1",
      "prefix": "",
      "domain": "https://cdn.example.com"
    }
  }
}
```

| 字段 | 含义 |
| --- | --- |
| `endpoint` | 自定义 endpoint(用 R2 / MinIO 时填),AWS S3 留空 |
| `bucket` | 桶名 |
| `access_key` / `secret_key` | 访问凭证 |
| `region` | 区域(如 `us-east-1`),默认 `us-east-1` |
| `prefix` | 对象 key 前缀,例如 `photos/2025/` |
| `domain` | CDN 域名,用于生成对外 URL;留空则返回 S3 原 URL |

### `upload.ftp.*` / `upload.sftp.*`

FTP / SFTP 账号信息。SFTP 还可以用 `key_path` 指定私钥文件。

### `upload.proxy.*`

走代理时配置。

```json
{
  "upload": {
    "proxy": {
      "enabled": true,
      "type": "socks5",
      "host": "127.0.0.1",
      "port": 7890,
      "username": "",
      "password": ""
    }
  }
}
```

`type` 可以是 `socks5` 或 `http`(HTTP-CONNECT)。S3 也支持代理,会传给
`reqwest` 客户端。

### `upload.custom_path`

想把每次上传放到一个固定子目录下时,填这里,例如 `artist/album`。程序会
把它拼到协议对应的基础路径上(S3 prefix、FTP remote_dir、SFTP remote_dir)。

### `prepare.rename_images` / `prepare.rename_videos`

`prepare` 步骤是否按 `0001.jpg` / `video001.mp4` 规则重命名。默认 `true`。
如果想保留原始文件名,改成 `false`。

### `language` / `theme`

`language`:`zh` 或 `en`(影响界面文本)。
`theme`:目前仅占位,默认 `light`。

---

## 交互模式(TUI)

### 启动

```bash
./imagecompression              # 用内置默认配置启动
./imagecompression              # Windows 下是 ImageCompression.exe
```

### 布局说明

| 列 | 作用 |
| --- | --- |
| 左列(Parent) | 显示当前目录的父目录,以及 Backspace 返回提示 |
| 中列(Current dir) | 当前目录的文件/子目录列表,选中项高亮 |
| 右列(Preview & Status) | 扫描结果、压缩结果、状态信息、快捷键提示 |

### 完整按键清单

| 按键 | 作用 |
| --- | --- |
| `j` / `↓` | 选中下一项 |
| `k` / `↑` | 选中上一项 |
| `Enter` | 进入子目录,或选中当前文件 |
| `Backspace` | 返回上级目录 |
| `r` | 扫描当前目录(后台) |
| `p` | 整理(后台,需要先扫描过) |
| `c` | 压缩(后台,用当前配置参数) |
| `,` | 打开设置 overlay |
| `h` | 打开/关闭帮助 overlay |
| `q` | 退出(带确认) |

### 设置 overlay(按 `,` 打开)

```
⚙ 设置 (pikpaktui 风格) - s 保存, Esc 取消, j/k 选择

   格式: avif
 > AVIF 质量上限: 40
   avifenc 路径: (PATH)
   准备重命名图片: true
   递归: (在 CLI/TUI 操作时控制)
```

| 按键 | 作用 |
| --- | --- |
| `j` / `↓` | 下一项 |
| `k` / `↑` | 上一项 |
| `Space` / `Enter` | 切换/修改当前项 |
| `s` | 保存到 `~/.imagecompression/config.json` |
| `Esc` | 取消并返回 |

修改后记得按 `s` 保存,否则重启后会丢失。

### 工作流示例:从扫描到压缩

1. 用 `j/k` 导航到目标目录,按 `Enter` 进入。
2. 按 `r` 扫描,看右侧"图片 / 视频 / 其他"的统计。
3. (可选)按 `p` 整理一份到 `_prepared` 目录。
4. 按 `c` 压缩,完成后右侧会显示节省百分比。
5. 退出后,新压缩好的文件在 `<input>_compressed/` 目录下。

---

## 命令行模式(CLI)

### 适用场景

- 写脚本,定时批量处理图片。
- 让 Agent / LLM 自动跑流程(此时务必加 `--json` 输出)。
- 远程 SSH 到服务器上跑批处理。
- CI/CD 中压缩资源。

### 总体语法

```bash
imagecompression [options] <command> [command-options]
```

无参数 → TUI。带子命令 → CLI。

### 全局选项

| 选项 | 效果 |
| --- | --- |
| `--help` / `-h` | 帮助 |
| `--version` / `-V` | 版本号 |

### 子命令一览

| 命令 | 作用 | 必填 |
| --- | --- | --- |
| `scan` | 扫描目录,统计图片/视频/其他数量 | `--input` |
| `prepare` | 重命名 + 复制到目标目录 | `--input` |
| `compress` | 批量压缩 | `--input` |
| `upload` | 上传到 S3 / FTP / SFTP | `--input` |
| `all` | 扫描 → 整理 → 压缩 →(可选)上传 | `--input` |

每个子命令都支持 `--json`,输出 JSON Lines 事件流(下面有详细示例)。

### `scan`

```bash
imagecompression scan --input ./photos
```

输出:

```
目录: ./photos
图片: 12
视频: 3
其他: 0
子目录: 4
总体积: 123456 bytes
```

加 `--json` 后是单个 JSON 对象,便于程序解析。

### `prepare`

```bash
imagecompression prepare \
  --input ./raw \
  --output ./prepared
```

把 `./raw` 下的图片重命名为 `0001.jpg`、`0002.jpg` …;视频重命名为
`video001.mp4`、`video002.mp4` …;子目录结构镜像到 `./prepared`。

常用选项:

- `--no-rename`:保留原始文件名。
- `--overwrite`:允许覆盖已有目标(默认遇到同名会报错)。

不传 `--output` 时,默认是 `<input>_prepared`。

### `compress`

```bash
imagecompression compress \
  --input ./prepared \
  --output ./compressed \
  --format avif \
  --quality 35 \
  --speed 6
```

| 选项 | 默认 | 含义 |
| --- | --- | --- |
| `--format` | `avif` | `avif` / `webp` / `jpeg` |
| `--quality` | `35` | 编码质量(含义因格式而异) |
| `--min-quality` | `20` | AVIF `--min` |
| `--speed` | `6` | AVIF 编码速度(0–10) |
| `--workers` | `1` | 并发 worker 数(AVIF 强制 1) |
| `--avifenc` | _(空)_ | avifenc 工具目录,不在 PATH 时用 |
| `--overwrite` | `false` | 覆盖已有输出 |
| `--json` | `false` | 输出 JSON Lines |

### `upload`

```bash
imagecompression upload --input ./compressed
```

读取 `~/.imagecompression/config.json` 的 `upload` 段,把所有文件上传到
配置的远端。可以用 `--config /path/to/other.json` 指定其他配置文件。

### `all`(一条龙)

```bash
imagecompression all \
  --input ./raw \
  --format avif --quality 35 \
  --upload
```

依次执行 scan → prepare → compress →(可选)upload。`--upload` 不传时
只跑到压缩为止。

### 退出码

| 码 | 含义 |
| --- | --- |
| `0` | 全部成功 |
| `1` | 至少一个文件失败 |
| `2` | 参数/用法错误 |

---

## 典型场景

### 场景 1:把一批手机照片压成 AVIF

```bash
imagecompression compress \
  --input ~/Pictures/iPhone-2025-06 \
  --output ~/Pictures/iPhone-2025-06-avif \
  --format avif --quality 35 --speed 6
```

体积通常能砍掉 60–80%,画质肉眼几乎无差。

### 场景 2:先把散乱的照片整理成编号形式

```bash
imagecompression prepare \
  --input ~/Pictures/unsorted \
  --output ~/Pictures/sorted
```

之后 `~/Pictures/sorted` 下:

```
0001.jpg   (原图 IMG_0001.JPG)
0002.jpg   (原图 IMG_0002.JPG)
video001.mp4   (原图 IMG_0042.MOV)
...
```

### 场景 3:缩放后再压缩(节省更多空间)

编辑 `~/.imagecompression/config.json`:

```json
{
  "compress": {
    "format": "avif",
    "resize_mode": "long_edge",
    "resize_value": 1920,
    "keep_aspect_ratio": true
  }
}
```

之后 `compress` 会把所有图片缩放到最长边 1920px 再压 AVIF。

### 场景 4:上传到 S3

编辑 `~/.imagecompression/config.json`:

```json
{
  "upload": {
    "protocol": "s3",
    "s3": {
      "endpoint": "",
      "bucket": "my-photos",
      "access_key": "AKIA...",
      "secret_key": "...",
      "region": "ap-east-1",
      "prefix": "2025/",
      "domain": "https://photos.example.com"
    }
  }
}
```

然后:

```bash
imagecompression upload --input ./compressed
```

完成后 `uploaded.txt`(若用 `--json` 时)或屏幕会显示每个文件的最终 URL,
形如 `https://photos.example.com/2025/0001.avif`。

### 场景 5:上传到 R2 / MinIO(自定义 endpoint)

```json
{
  "upload": {
    "protocol": "s3",
    "s3": {
      "endpoint": "https://<accountid>.r2.cloudflarestorage.com",
      "bucket": "my-bucket",
      "access_key": "...",
      "secret_key": "...",
      "region": "auto"
    }
  }
}
```

Cloudflare R2 用 `auto` 作为 region;其他 S3 兼容存储按其文档填 region。

### 场景 6:通过 SOCKS5 代理上传

```json
{
  "upload": {
    "proxy": {
      "enabled": true,
      "type": "socks5",
      "host": "127.0.0.1",
      "port": 7890
    }
  }
}
```

代理对 S3、FTP、SFTP 都生效(S3 走 `reqwest` 代理,FTP/SFTP 走
SOCKS5/HTTP-CONNECT 隧道)。

### 场景 7:写个 shell 脚本批量处理

```bash
#!/bin/bash
set -e

ICLI=~/bin/imagecompression

for DIR in ~/Pictures/2025-*/; do
  echo "处理 $DIR"
  "$ICLI" prepare --input "$DIR" --output "${DIR%/}_prepared"
  "$ICLI" compress --input "${DIR%/}_prepared" \
                   --output "${DIR%/}_avif" \
                   --format avif --quality 35
done
```

---

## 进阶技巧

### 用 `--json` 让进度可解析

加 `--json` 后,所有进度信息变成 JSON Lines 事件流:

```bash
imagecompression --json compress --input ./photos --format avif --quality 35
```

输出(每行一条 JSON):

```jsonc
{"event":"start","phase":"compress","total":45}
{"event":"progress","phase":"compress","current":1,"total":45,"file":"0001.jpg","speed":0.4,...}
{"event":"error","phase":"compress","current":2,"total":45,"file":"0002.jpg","error":"..."}
{"event":"done","phase":"compress","total":45,"compressed":43,"skipped":0,"failed":2,
 "originalSize":1234567,"compressedSize":654321,"savedPercent":47.0,"elapsed":12.3}
```

配合 `jq` 做实时监控:

```bash
imagecompression --json compress --input ./photos --format avif \
  | jq -c 'select(.event=="progress") | {file: .currentFile, speed}'
```

把成功上传的 URL 收集到文件:

```bash
imagecompression --json upload --input ./out \
  | jq -r 'select(.url != null) | .url' > uploaded.txt
```

### 备份/迁移配置

整个配置文件就一个 `config.json`,拷贝即可。

### 多套配置

```bash
imagecompression upload --input ./out --config ~/.imagecompression/work.json
imagecompression upload --input ./out --config ~/.imagecompression/personal.json
```

适用于工作/个人/客户多账号场景。

### 干运行

先用 `scan` 看文件数,再决定是否执行 prepare/compress:

```bash
imagecompression scan --input ./huge-folder
# 看输出:图片 12345 / 视频 100 / 其他 5
# 决定开始压缩
imagecompression compress --input ./huge-folder --format avif --quality 35
```

### 大量失败时怎么办?

`compress` 默认遇到错误继续处理其他文件,失败的会被列在 `errors` 字段
里(`--json`)或打印在最后(非 `--json`)。可以:

1. 看错误信息,判断是图片损坏还是编码器问题。
2. 用 `--conflict-strategy skip`(在 config 中)跳过已存在的目标。
3. 用 `--overwrite` 重跑,覆盖之前部分完成的输出。

---

## 常见问题 FAQ

### Q1:双击 Windows .exe 后窗口一闪而过?

说明它不是 GUI 程序。在 PowerShell 或 cmd 中运行,而不是双击:

```powershell
cd C:\path\to\folder
.\ImageCompression.exe
```

不带任何参数会进入 TUI,带子命令则执行后退出。

### Q2:AVIF 压缩报 "avifenc: command not found"?

`avifenc` 不在 PATH 上,或 `avifenc_path` 配置错了。

- Windows:把归档里的 `windows-artifacts/` 整个目录解压到固定位置,例如
  `C:\tools\avif\`,然后配置:

  ```json
  { "avifenc_path": "C:\\tools\\avif" }
  ```

- Linux:`apt install libavif-bin`。
- macOS:`brew install libavif` 或从
  [官方 release](https://github.com/AOMediaCodec/libavif/releases) 下载。

### Q3:WebP 压缩报 "cwebp: command not found"?

类似 Q2。安装 webp 工具:

- Windows:[libwebp release](https://storage.googleapis.com/downloads.webmproject.org/releases/webp/index.html)
  下载,解压到 PATH 目录。
- Linux:`apt install webp`。
- macOS:`brew install webp`。

### Q4:SFTP 上传报 "该二进制未启用 sftp feature"?

你下载的预编译包没有 SFTP 支持。SFTP 依赖 OpenSSL,Windows 上跨工具链
构建比较麻烦。两种解决方式:

1. 用 S3 或 FTP 代替。
2. 自己从源码构建并启用 SFTP feature(见 [DEPLOYMENT.md](./DEPLOYMENT.md))。

### Q5:S3 上传一直 403 SignatureDoesNotMatch?

签名路径与实际 PUT 路径不一致。检查:

- 自定义 endpoint 时必须用 path-style: `https://endpoint/bucket/key`。
- AWS S3 走 virtual-host style: `https://bucket.s3.amazonaws.com/key`。
- 桶名、region、access_key / secret_key 是否一致。
- 路径里有空格 / 中文时,程序会自动 percent-encode,不应该出问题;但
  access_key / secret_key 末尾多了空格 / 换行会触发这个问题。

### Q6:压缩很慢?

- AVIF 本来就慢,`--speed` 调到 `10` 可以快 5–10 倍,但文件会略大。
- WebP / JPEG 调高 `--workers` 利用多核(AVIF 不行,会内部争用)。
- 用 `--resize-mode long_edge --resize-value 1920` 先缩放,小图压缩
  快得多。

### Q7:输出文件比原图还大?

通常是图片本身已经很小(< 100KB),或者质量参数太高。
试试把 `--quality` 调低(AVIF `35` → `50`),或者直接选 `jpeg`
(`webp_jpeg.quality: 70` 是个保险值)。

### Q8:如何恢复默认配置?

```bash
# Windows
del %USERPROFILE%\.imagecompression\config.json

# Linux / macOS
rm ~/.imagecompression/config.json
```

下次启动会自动用内置默认值重建。

### Q9:程序占多少磁盘?有缓存目录吗?

不会在磁盘上留缓存。中间临时文件(缩放后的 PNG)处理完立即删除。
最终输出在 `--output` 指定的目录里。

### Q10:会修改原图吗?

不会。`compress` / `prepare` / `upload` 都是**只读原文件**,输出到
`--output`。只有 `--overwrite` 且 `--output` 等于 `--input` 时才可能
覆盖原文件 —— 请确认你确实想这么做。

---

## 故障排查

| 症状 | 可能原因 | 解决方案 |
| --- | --- | --- |
| `error: linker not found`(Linux 源码编译) | 缺 build-essential | `apt install build-essential pkg-config libssl-dev` |
| `failed to run custom build command for openssl-sys` | OpenSSL 头文件缺失 | `apt install libssl-dev` |
| `avifenc: command not found` | 编码器没装/没在 PATH | 见 FAQ Q2 |
| `cwebp: command not found` | webp 工具没装 | 见 FAQ Q3 |
| `该二进制未启用 sftp feature` | 预编译包不含 SFTP | 见 FAQ Q4 |
| S3 PUT 返回 403 | 签名路径错或凭据错 | 见 FAQ Q5 |
| 压缩输出为空 / 0 个文件 | `--input` 目录不存在或无图片 | 检查路径是否正确,目录里是否有 `.jpg` / `.png` 等 |
| TUI 启动后乱码 | 终端不支持 UTF-8 或 Unicode | Windows 用 Windows Terminal;Linux/macOS 确保 `LANG=en_US.UTF-8` |
| TUI 启动后颜色丢失 | 终端不支持 ANSI | 用现代终端(Windows Terminal、iTerm2、gnome-terminal 等) |
| Release 包校验和不匹配 | 下载不完整 | 用 `sha256sum -c sha256sums.txt` 重下 |
| macOS 提示"无法验证开发者" | 没授权 | 系统设置 → 隐私与安全性 → 仍要打开 |

如果以上都没解决,在 GitHub Issues 提单时附上:

- 操作系统与版本。
- 完整命令行(去掉敏感信息)。
- 完整的错误输出。
- `imagecompression --version` 的输出。