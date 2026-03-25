# Image Compression

> 高性能批量图片压缩平台 — GUI + CLI 双模式

**[English](./README_EN.md)** | 中文

## ✨ 功能亮点

| 特性 | 说明 |
|---|---|
| 🖼️ 多格式 | 输入: JPG/PNG/WebP/HEIC/TIFF/BMP/GIF/AVIF — 输出: AVIF/WebP/JPEG |
| ⚡ 高性能 | 并行处理 + avifenc 原生多线程 + 实时速度显示 |
| 📐 AVIF 全参数 | YUV 420/422/444 · 位深 8/10/12 · Alpha 独立质量 · 无损 · 渐进式 |
| 🎯 预设模板 | web / mobile / lossless / max_compress / hdr 五种一键配置 |
| 📁 批量处理 | 递归子目录 · 保持目录结构 · 跳过/覆盖/重命名冲突策略 |
| 🔍 预览对比 | 压缩前后并排预览 · 文件大小柱状图 |
| ☁️ 云上传 | S3 / FTP / SFTP · 自定义域名 · 递归子目录 · 代理支持 |
| 🎨 三种主题 | 浅色 / 深色 / 灰色 |
| 🌐 双语 | 中文 / 英文界面 |

---

## 📦 安装部署

### 环境要求

- **Python** 3.11+
- **avifenc** (libavif) — AVIF 压缩必须

### 第一步：安装 avifenc

```bash
# Windows (推荐 scoop)
scoop install libavif

# Windows (手动)
# 从 https://github.com/AOM-AV1-Codec/libavif/releases 下载
# 将 avifenc.exe 放入 PATH 或在设置中指定路径

# macOS
brew install libavif

# Linux (Ubuntu/Debian)
apt install libavif-bin

# Linux (Arch)
pacman -S libavif
```

### 第二步：安装依赖

```bash
git clone https://github.com/SakurajimMai/ImageCompression.git
cd ImageCompression
pip install -r requirements.txt
```

### 第三步：启动

```bash
# GUI 模式
cd src
python main.py

# CLI 模式
python cli.py --help
```

---

## 🖥️ GUI 使用指南

### 页面说明

| Tab | 功能 |
|---|---|
| **准备** | 文件重命名 + 目录整理（支持递归，子目录独立编号） |
| **压缩** | 核心压缩功能，支持 AVIF/WebP/JPEG |
| **上传** | 压缩后一键上传至 S3/FTP/SFTP |
| **设置** | avifenc 路径 · 主题 · 语言 |
| **说明** | 内置帮助文档 |

### 压缩参数详解

#### AVIF 参数

| 参数 | 范围 | 默认值 | 说明 |
|---|---|---|---|
| Quality 下限 | 0-63 | 20 | avifenc `--min`，值越低压缩越多 |
| Quality 上限 | 0-63 | 40 | avifenc `--max`，决定最终质量 |
| 速度 | 0-10 | 6 | 0=最慢最高质量，10=最快 |
| 线程 | 1-N / 全部 | 全部 | 编码并行线程数 |
| YUV | 420/422/444 | 420 | 420=最小体积，444=最高质量 |
| 位深 | 8/10/12 | 8 | 8=标准，10=HDR，12=专业 |
| Alpha 独立质量 | 可选 | 关闭 | 透明通道独立控制 |
| 无损压缩 | 开/关 | 关 | 完全无损，体积较大 |
| 渐进式输出 | 开/关 | 关 | 渐进加载（需 libavif 1.1+） |

#### WebP / JPEG 参数

| 参数 | 范围 | 默认值 | 说明 |
|---|---|---|---|
| Quality | 1-100 | 80 | 压缩质量 |
| 无损 (WebP) | 开/关 | 关 | 仅 WebP 支持 |

#### 缩放参数

| 模式 | 说明 |
|---|---|
| 不缩放 | 保持原始分辨率 |
| 宽度 | 固定宽度，高度按比例 |
| 高度 | 固定高度，宽度按比例 |
| 百分比 | 按比例缩放（如 50%） |
| 长边 | 限制长边最大值，等比缩放 |
| 短边 | 限制短边最大值，等比缩放 |

> ⚠️ **注意**：所有缩放模式都是等比缩放，不会裁剪图片。

#### 其他选项

| 参数 | 说明 |
|---|---|
| 覆盖原文件 | 压缩后替换原文件（扩展名变化时自动删除原文件） |
| 输出到新目录 | 压缩结果输出到指定目录 |
| 递归子目录 | 处理所有子目录中的图片 |
| 并行数 | 同时处理的文件数（AVIF 使用内部多线程，外部串行） |

### AVIF Quality 对照表

AVIF 的 quality 刻度与 JPEG 不同：

| AVIF Quality 上限 | ≈ JPEG 等价 | 适用场景 |
|:---:|:---:|:---|
| 60-63 | 95+ | 原图存档、印刷 |
| 45-55 | 85-92 | 高质量网站展示 |
| 35-45 | 75-85 | 一般网站展示 |
| 25-35 | 65-75 | 缩略图、移动端 |
| 15-25 | 50-65 | 极致压缩 |

---

## ⌨️ CLI 使用指南

### 基本用法

```bash
# 基本压缩（AVIF 默认）
python cli.py compress ./photos -o ./output

# 指定格式和质量
python cli.py compress ./photos -f avif -q 40 -o ./output

# 使用预设
python cli.py compress ./photos --preset web

# 递归 + 覆盖原文件
python cli.py compress ./photos -f avif --recursive --overwrite

# 指定 avifenc 路径
python cli.py compress ./photos --avifenc /path/to/avifenc

# 无损 + HDR
python cli.py compress ./photos --lossless --depth 10 --yuv 444
```

### 其他命令

```bash
# 查看图片信息
python cli.py info photo.jpg

# 扫描目录统计
python cli.py scan ./photos -r

# 查看预设列表
python cli.py presets
```

### CLI 参数一览

| 参数 | 缩写 | 说明 |
|---|---|---|
| `--format` | `-f` | 输出格式: avif / webp / jpeg |
| `--output` | `-o` | 输出目录 |
| `--quality` | `-q` | 压缩质量 (0-100) |
| `--speed` | `-s` | AVIF 编码速度 (0-10) |
| `--preset` | | 预设模板 |
| `--lossless` | | 无损压缩 |
| `--recursive` | `-r` | 递归子目录 |
| `--overwrite` | | 覆盖原文件 |
| `--workers` | `-j` | 并行数 |
| `--yuv` | | YUV 格式 (420/422/444) |
| `--depth` | | 位深 (8/10/12) |
| `--avifenc` | | avifenc 路径 |

---

## 📋 预设模板

| 预设 | Quality | Speed | YUV | 位深 | 说明 |
|---|---|---|---|---|---|
| `web` | 55 | 6 | 420 | 8 | 网页展示，平衡质量与大小 |
| `mobile` | 60 | 6 | 420 | 8 | 移动端优化 |
| `lossless` | 100 | 4 | 444 | 10 | 完全无损 |
| `max_compress` | 30 | 4 | 420 | 8 | 极致压缩 |
| `hdr` | 65 | 4 | 444 | 10 | HDR 模式 |

---

## ☁️ 上传配置

### SFTP

| 字段 | 说明 | 示例 |
|---|---|---|
| 主机 | 服务器地址 | `192.168.1.100` |
| 端口 | SSH 端口 | `22` |
| 用户名 | SSH 用户 | `deploy` |
| 密码/私钥 | 认证方式 | — |
| 远程目录 | 上传到的绝对路径 | `/var/www/uploads/xxxx` |
| 访问域名 | CDN 或网站域名 | `https://cdn.example.com` |
| 域名根目录 | 域名对应的服务器路径 | `/var/www` |

**URL 生成规则**：`域名` + (`远程目录` - `域名根目录`) + `/文件名`

示例：`https://cdn.example.com/uploads/xxxx/0001.avif`

### S3

| 字段 | 说明 |
|---|---|
| Endpoint | S3 端点 URL |
| Bucket | 存储桶名称 |
| Access Key | 访问密钥 |
| Secret Key | 密钥 |
| 前缀 | 远程路径前缀 |
| 自定义域名 | CDN 域名（可选） |

---

## 📂 项目结构

```
ImageCompression/
├── src/
│   ├── main.py              # GUI 入口
│   ├── cli.py               # CLI 入口 (click)
│   ├── config.py            # 配置管理 (JSON 持久化)
│   ├── core/                # 业务逻辑
│   │   ├── compress.py      # 压缩逻辑
│   │   ├── prepare.py       # 文件准备/重命名
│   │   └── upload.py        # 上传 (S3/FTP/SFTP)
│   ├── engine/              # 核心引擎
│   │   ├── formats/         # 格式处理器插件
│   │   │   ├── base.py      # FormatHandler 抽象基类
│   │   │   ├── registry.py  # 自动发现注册表
│   │   │   ├── avif.py      # AVIF (avifenc)
│   │   │   ├── webp.py      # WebP (Pillow)
│   │   │   └── jpeg.py      # JPEG (Pillow)
│   │   ├── pipeline.py      # 批量调度
│   │   ├── scanner.py       # 目录扫描
│   │   ├── presets.py       # 预设模板
│   │   └── resizer.py       # 缩放引擎
│   └── ui/                  # PySide6 GUI
│       ├── main_window.py   # 主窗口
│       ├── compress_tab.py  # 压缩页
│       ├── upload_tab.py    # 上传页
│       ├── theme.py         # 主题系统
│       └── i18n.py          # 国际化
├── tests/                   # 测试 (54 用例)
├── docs/                    # 文档
└── requirements.txt
```

## 🔧 技术栈

| 组件 | 技术 |
|---|---|
| GUI | PySide6 (Qt6) |
| CLI | click |
| AVIF 编码 | avifenc (libavif) |
| 图片处理 | Pillow + pillow-heif |
| 云上传 | boto3 (S3) · paramiko (SFTP) · ftplib (FTP) |
| 配置 | JSON (dataclass) |

## 📄 协议

MIT License
