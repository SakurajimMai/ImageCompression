# Go/Wails 版本说明

当前仓库已经完成 Go/Wails 替换，旧 Python/PySide6 代码、PyInstaller 配置和旧文档计划已移除。

## 目标

- 使用 Go 承载准备、压缩、上传等核心逻辑。
- 使用 Wails + React/Vite 提供桌面界面。
- 通过 Windows 单 exe 分发，减少旧 Python/PyInstaller 运行时目录体积。

## 根目录结构

- `app.go`、`main.go`：Wails 桌面应用入口和后端绑定。
- `internal/compress`：AVIF/WebP/JPEG 压缩、缩放、预览。
- `internal/config`：配置读写、默认值、旧代理 URL 兼容。
- `internal/core`：目录扫描。
- `internal/prepare`：准备计划和执行。
- `internal/upload`：S3/FTP/SFTP 上传，含 SOCKS5 和 HTTP CONNECT 代理。
- `internal/workflow`：准备、压缩、上传串联。
- `frontend`：React/Vite 工作台。

## 验证命令

```powershell
go test ./...
```

```powershell
cd frontend
npm run build
```

```powershell
go run github.com/wailsapp/wails/v2/cmd/wails@v2.10.2 build
```

## 外部编码器

- AVIF 依赖系统中的 `avifenc`。
- WebP 依赖系统中的 `cwebp`。
- JPEG 使用 Go 标准库编码。

## 上传代理

代理是全局上传配置，适用于 S3、FTP 和 SFTP：

- `socks5`：通过 SOCKS5 拨号。
- `http`：通过 HTTP CONNECT 建立隧道。
- 支持用户名和密码。

旧配置中的 `proxy.url` 会在加载时解析到结构化字段；实际构造代理 URL 时优先使用结构化字段。
