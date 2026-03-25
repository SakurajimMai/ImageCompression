# Image Compression 桌面工具设计文档

> **日期**: 2026-03-24 | **状态**: 设计中

## 1. 背景与目标

COS 资源站的图片资源存在双重需求：
- **网盘分发**：保留完整原始内容（图片+视频），供用户下载
- **网站展示**：使用压缩后的 AVIF/WebP 图片，减少带宽和加载时间

目前这个过程完全依赖手动操作（重命名、去 EXIF、压缩、上传），效率低且易出错。

**目标**：构建一个 PySide6 桌面 GUI 工具，自动化图片准备、压缩和上传流程。

## 2. 工作流设计

```
原始文件夹（混合图片+视频）
        │
        ▼
┌─ Image Compression ────────────────────────────┐
│                                                 │
│  📁 准备 Tab                                    │
│  ├── 图片重命名: 0001.jpg, 0002.jpg, ...        │
│  ├── 视频重命名: video001.mp4, video002.mp4, ...│
│  └── 清除 EXIF 信息                             │
│       ↓ 输出: ready/ 目录                       │
│       → [手动] 打包上传到网盘                    │
│                                                 │
│  🗜️ 压缩 Tab                                   │
│  ├── 过滤掉视频，仅处理图片                     │
│  ├── 压缩为 AVIF / WebP / JPEG (可选)          │
│  └── 输出到新目录或覆盖原文件                   │
│       ↓ 输出: compressed/ 目录                  │
│                                                 │
│  ☁️ 上传 Tab                                    │
│  ├── 上传到 S3 / FTP / SFTP                    │
│  ├── 支持代理配置                               │
│  └── 输出 URL 列表                              │
│       → [手动] 在后台创建文章，粘贴 URL         │
└─────────────────────────────────────────────────┘
```

## 3. 技术架构

### 3.1 技术栈

| 组件 | 技术 | 理由 |
|------|------|------|
| GUI 框架 | PySide6 (Qt6) | 原生体验，跨平台，可打包 exe |
| AVIF 编码 | avifenc (libavif) | 业界最佳 AVIF 编码质量和速度 |
| 图片处理 | Pillow | EXIF 清除、格式检测、WebP/JPEG 压缩 |
| S3 上传 | boto3 | AWS S3 兼容存储标准库 |
| FTP/SFTP | ftplib / paramiko | Python 标准库 / SSH 文件传输 |
| 打包 | PyInstaller | 打包为单文件 exe |

### 3.2 项目结构

```
ImageCompression/           # 独立项目根目录
├── docs/
│   └── plans/
│       └── 2026-03-24-image-compression-design.md  # 本文件
├── src/
│   ├── main.py             # 应用入口
│   ├── config.py           # 配置管理（JSON 持久化）
│   ├── core/
│   │   ├── prepare.py      # 重命名 + EXIF 清除逻辑
│   │   ├── compress.py     # AVIF/WebP/JPEG 压缩（调用 avifenc）
│   │   └── upload.py       # S3/FTP/SFTP 上传逻辑
│   ├── ui/
│   │   ├── main_window.py  # 主窗口（标签页布局）
│   │   ├── prepare_tab.py  # 准备页 UI
│   │   ├── compress_tab.py # 压缩页 UI
│   │   ├── upload_tab.py   # 上传页 UI
│   │   ├── settings_tab.py # 设置页 UI
│   │   └── widgets/
│   │       ├── progress.py     # 进度条组件
│   │       └── url_output.py   # URL 列表输出组件
│   └── resources/
│       └── icon.ico        # 应用图标
├── requirements.txt        # Python 依赖
├── build.spec              # PyInstaller 打包配置
└── README.md               # 项目说明
```

### 3.3 核心模块设计

#### 📁 准备模块 (core/prepare.py)

- **输入**：原始文件夹路径
- **输出**：重命名后的文件夹
- **逻辑**：
  - 扫描文件夹，按扩展名分类（图片 vs 视频）
  - 图片格式：`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`, `.tiff`
  - 视频格式：`.mp4`, `.mov`, `.avi`, `.mkv`, `.wmv`
  - 按文件名自然排序后重命名：图片 `0001~9999`，视频 `video001~video999`
  - 用 Pillow 清除 EXIF：读取 → 去 EXIF → 保存
  - 输出到新目录或覆盖原文件（用户选择）

#### 🗜️ 压缩模块 (core/compress.py)

- **输入**：图片文件夹路径 + 压缩参数
- **输出**：压缩后的图片文件夹
- **支持格式**：AVIF / WebP / JPEG（GUI 可选）
- **AVIF 参数**（通过 GUI 调节）：
  - `--min` / `--max`：质量范围（默认 20~40）
  - `--speed`：编码速度 0-10（默认 6）
  - `-j`：线程数（默认 all）
- **WebP 参数**：通过 Pillow，quality 可调
- **JPEG 参数**：通过 Pillow，quality 可调
- **自动跳过视频文件**
- **并行处理**：多线程分发 avifenc 子进程

#### ☁️ 上传模块 (core/upload.py)

- **协议支持**：S3 / FTP / SFTP
- **代理支持**：HTTP/SOCKS5 代理
- **远程路径前缀**：可配置（如 `/2026/03/`）
- **输出**：上传完成后生成 URL 列表，支持一键复制

### 3.4 配置持久化

配置文件保存在 `~/.imagecompression/config.json`：

```json
{
  "last_input_dir": "C:/cosplay/xxx",
  "output_mode": "new_directory",
  "compress": {
    "format": "avif",
    "avif_min": 20,
    "avif_max": 40,
    "avif_speed": 6,
    "avif_threads": "all"
  },
  "upload": {
    "protocol": "s3",
    "s3": {
      "endpoint": "https://...",
      "bucket": "images",
      "access_key": "...",
      "secret_key": "...",
      "prefix": "/2026/03/"
    },
    "proxy": {
      "enabled": false,
      "url": "socks5://127.0.0.1:7890"
    }
  }
}
```

## 4. GUI 界面设计

- 标签页切换：准备 | 压缩 | 上传 | 设置
- 底部固定：进度条 + 日志输出区域
- 支持文件夹拖拽
- 一键执行按钮（串联 准备→压缩→上传）
- 每个 Tab 可独立使用

## 5. 实现优先级

| 优先级 | 功能 |
|--------|------|
| **P0** | 准备模块（重命名 + EXIF 清除） |
| **P0** | AVIF 压缩（avifenc 调用 + 进度展示） |
| **P0** | S3 上传 + URL 输出 |
| **P0** | PySide6 GUI（标签页布局 + 参数调节） |
| **P1** | WebP/JPEG 压缩 |
| **P1** | FTP/SFTP 上传 |
| **P1** | 代理配置 |
| **P1** | 配置持久化 + 预设管理 |
| **P2** | PyInstaller 打包 exe |
| **P2** | 一键串联执行 |
