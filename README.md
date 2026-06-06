# Image Compression

Image Compression 是一个基于 Go + Wails + React/Vite 的桌面图片工作台，用于完成图片准备、压缩和上传流程。当前仓库只保留 Go/Wails 版本，旧 Python/PySide6 实现已移除。

## 功能

- 目录扫描：识别图片、视频和其他文件，支持递归扫描。
- 准备流程：图片/视频重命名、输出目录规划、批量复制执行。
- 图片压缩：支持 AVIF、WebP、JPEG。
- 缩放策略：支持不缩放、按宽度、按高度、百分比、长边、短边、fit、fill、exact。
- 上传协议：支持 S3、FTP、SFTP。
- 上传代理：支持 SOCKS5 与 HTTP CONNECT，支持用户名和密码。
- 桌面分发：通过 Wails 构建 Windows 单 exe。

## 环境要求

| 依赖 | 说明 |
| --- | --- |
| Go 1.23+ | 后端核心与 Wails 构建 |
| Node.js 22+ | React/Vite 前端构建 |
| Wails v2.10.2 | 桌面应用构建工具 |
| avifenc | AVIF 压缩需要 |
| cwebp | WebP 压缩需要 |

JPEG 压缩由 Go 标准库直接完成，不依赖外部编码器。

## 开发命令

```powershell
go test ./...
```

```powershell
cd frontend
npm install
npm run build
```

```powershell
go run github.com/wailsapp/wails/v2/cmd/wails@v2.10.2 build
```

也可以先安装 Wails CLI：

```powershell
go install github.com/wailsapp/wails/v2/cmd/wails@v2.10.2
wails build
```

构建产物位于：

```text
build/bin/ImageCompression.exe
```

## 项目结构

```text
.
├── app.go                 # Wails 后端绑定接口
├── main.go                # Wails 应用入口
├── go.mod
├── go.sum
├── wails.json
├── internal/
│   ├── compress/          # AVIF/WebP/JPEG 压缩、缩放、预览
│   ├── config/            # 配置结构、加载、保存、代理兼容
│   ├── core/              # 目录扫描
│   ├── prepare/           # 准备计划与执行
│   ├── upload/            # S3/FTP/SFTP 上传与代理拨号
│   └── workflow/          # 准备-压缩-上传串联流程
├── frontend/
│   ├── src/               # React 工作台
│   ├── package.json
│   └── package-lock.json
├── docs/
│   └── GO_WAILS_REWRITE.md
└── .github/workflows/
    └── build.yml
```

## 配置

应用配置保存在用户目录：

```text
%USERPROFILE%\.imagecompression\config.json
```

代理配置以结构化字段为准：

- `type`: `socks5` 或 `http`
- `host`: 代理主机
- `port`: 代理端口
- `username`: 可选用户名
- `password`: 可选密码

旧配置里的 `url` 字段只用于兼容加载旧数据；保存和实际上传时以前端结构化字段为准。

## CI

GitHub Actions 会在 Windows runner 上执行：

1. 设置 Go 和 Node.js。
2. 运行 `go test ./...`。
3. 执行 `wails build`。
4. 打包 `build/bin/ImageCompression.exe` 为 release artifact。
