# 开发指南

> Image Compression 本地开发环境搭建与开发规范

## 环境要求

| 工具 | 版本 | 用途 |
|---|---|---|
| Python | 3.11+ | 运行时 |
| avifenc | 1.0+ (推荐 1.4+) | AVIF 编码 |
| pip | 最新 | 包管理 |
| Git | 最新 | 版本控制 |

## 安装步骤

```bash
# 1. 克隆项目
git clone <repo-url>
cd ImageCompression

# 2. 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# 3. 安装依赖
pip install -r requirements.txt
pip install click watchdog pillow-heif

# 4. 安装 avifenc
scoop install libavif    # Windows
brew install libavif     # macOS
apt install libavif-bin  # Ubuntu/Debian

# 5. 验证安装
avifenc --version
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"
```

## 运行

```bash
# GUI 模式
cd src
python main.py

# CLI 模式
cd src
python cli.py --help
python cli.py compress ./test_images -f avif --preset web
```

## 目录结构

```
src/
├── main.py              # GUI 入口 — QApplication + MainWindow
├── cli.py               # CLI 入口 — click 命令组
├── config.py            # Config dataclass + JSON 序列化
│
├── engine/              # 新架构核心（纯逻辑，无 UI 依赖）
│   ├── formats/
│   │   ├── base.py      # FormatHandler ABC + 数据模型
│   │   ├── registry.py  # 注册表 + 自动发现
│   │   ├── avif.py      # AVIF (subprocess avifenc)
│   │   ├── webp.py      # WebP (Pillow)
│   │   └── jpeg.py      # JPEG (Pillow)
│   ├── pipeline.py      # 批量调度（并行 + 重试 + 冲突）
│   ├── scanner.py       # 目录扫描
│   ├── stats.py         # 批量统计
│   ├── resizer.py       # 图片缩放
│   ├── metadata.py      # EXIF/ICC/XMP 处理
│   ├── presets.py       # 预设模板
│   └── watcher.py       # 文件夹监控 (watchdog)
│
├── core/                # 旧版模块（兼容，UI Tab 直接调用）
│   ├── compress.py      # 旧版压缩逻辑
│   ├── prepare.py       # 文件准备/重命名
│   └── upload.py        # S3/FTP/SFTP 上传
│
└── ui/                  # PySide6 GUI（仅依赖 engine + core + config）
    ├── main_window.py   # 主窗口 5 Tab
    ├── compress_tab.py  # 压缩页（486 行）
    ├── prepare_tab.py   # 准备页
    ├── upload_tab.py    # 上传页
    ├── settings_tab.py  # 设置页
    ├── help_tab.py      # 说明页 (HTML 富文本)
    ├── preview_dialog.py# 预览弹窗
    ├── theme.py         # 双主题 QSS
    ├── i18n.py          # 国际化 (150+ 条翻译)
    └── widgets/
        ├── progress.py  # 进度条组件
        └── url_output.py# URL 输出组件
```

## 代码规范

### 命名

- 文件名：`snake_case.py`
- 类名：`PascalCase`
- 函数/变量：`snake_case`
- 常量：`UPPER_SNAKE_CASE`

### 导入顺序

```python
# 1. 标准库
import os
from pathlib import Path

# 2. 第三方
from PySide6.QtWidgets import QWidget
from PIL import Image

# 3. 项目内部
from engine.formats.base import CompressParams
```

### Engine 层开发规范

- **无 UI 依赖** — engine/ 下的模块不得导入 PySide6
- **纯逻辑** — 只接收参数返回结果，不做 I/O 以外的副作用
- **回调模式** — 进度通知使用 `Callable` 回调，不使用 Qt Signal

### UI 层开发规范

- **防双击** — 所有操作按钮检查 `worker.isRunning()`
- **文件句柄** — Pillow 操作后使用 `with` 或显式 `close()`
- **主线程安全** — 耗时操作放 QThread，通过 Signal 更新 UI

## 添加新格式

1. 创建 `engine/formats/your_format.py`
2. 实现 `FormatHandler` 抽象基类
3. 在模块底部调用 `register_handler(YourHandler())`
4. 在 `registry.py` 的 `_auto_discover()` 中导入

```python
# engine/formats/jxl.py
from engine.formats.base import FormatHandler, CompressParams, CompressResult
from engine.formats.registry import register_handler

class JxlHandler(FormatHandler):
    @property
    def name(self) -> str: return "jxl"

    @property
    def display_name(self) -> str: return "JPEG XL"

    @property
    def extensions(self) -> list[str]: return [".jxl"]

    @property
    def supports_lossless(self) -> bool: return True

    @property
    def supports_alpha(self) -> bool: return True

    def compress(self, input_path, output_path, params):
        # 实现压缩逻辑
        ...

    def get_info(self, path):
        # 实现信息获取
        ...

register_handler(JxlHandler())
```

## 配置文件

路径：`~/.imagecompression/config.json`

```json
{
  "last_input_dir": "",
  "last_output_dir": "",
  "avifenc_path": "avifenc",
  "language": "zh",
  "theme": "light",
  "compress": {
    "format": "avif",
    "avif": { "min_quality": 20, "max_quality": 40, "speed": 6, "threads": "all" }
  },
  "upload": {
    "protocol": "s3",
    "s3": { "endpoint": "", "bucket": "", "access_key": "", "secret_key": "" }
  }
}
```

## 调试技巧

```bash
# 检查 avifenc 可用性
python -c "from core.compress import check_avifenc; print(check_avifenc())"

# 验证格式注册表
python -c "
import sys; sys.path.insert(0, 'src')
from engine.formats.registry import list_handlers
for h in list_handlers(): print(h.name, h.display_name)
"

# 验证预设
python -c "
import sys; sys.path.insert(0, 'src')
from engine.presets import list_presets
for p in list_presets(): print(p)
"
```

## 已知问题

1. **覆盖模式风险** — 覆盖原文件时若压缩失败可能丢失原文件
2. **FTP 多级目录** — ftplib 不支持递归创建多级目录
3. **配置明文** — S3/FTP 密码以明文存储在 config.json
