# Image Compression Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan in single-flow mode.

**Goal:** 构建一个 PySide6 桌面 GUI 工具，自动化图片准备（重命名+去EXIF）、压缩（AVIF/WebP/JPEG）和上传（S3/FTP/SFTP）流程。

**Architecture:** 独立桌面应用，core 层负责业务逻辑（准备/压缩/上传），ui 层负责 PySide6 GUI。核心处理在 QThread 中异步执行，通过信号机制更新进度。配置存储在 JSON 文件中。

**Tech Stack:** Python 3.10+ / PySide6 / avifenc (libavif) / Pillow / boto3 / paramiko

---

### Task 1: 项目初始化与依赖配置

**Files:**
- Create: `ImageCompression/requirements.txt`
- Create: `ImageCompression/src/main.py`
- Create: `ImageCompression/README.md`

**Step 1: 创建 requirements.txt**

```txt
PySide6>=6.6.0
Pillow>=10.0.0
boto3>=1.34.0
paramiko>=3.4.0
PySocks>=1.7.1
```

**Step 2: 创建应用入口 main.py**

```python
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Image Compression")
    app.setOrganizationName("ImageCompression")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

**Step 3: 创建 README.md**

基本项目说明，包含依赖安装和运行方法。

**Step 4: 安装依赖并验证**

Run: `cd ImageCompression && pip install -r requirements.txt`
Expected: 所有依赖安装成功

**Step 5: 验证 avifenc 是否可用**

Run: `avifenc --version`
Expected: 显示 avifenc 版本号（如未安装需提示用户安装）

---

### Task 2: 配置管理模块

**Files:**
- Create: `ImageCompression/src/config.py`

**Step 1: 实现配置管理类**

```python
# 配置类负责：
# - 从 ~/.imagecompression/config.json 读取配置
# - 保存配置到文件
# - 提供默认值
# - 包含所有可配置参数（压缩参数、上传参数、代理设置等）
```

功能要点：
- `load()` / `save()` 读写 JSON 配置文件
- 默认配置值：avif_min=20, avif_max=40, avif_speed=6, avif_threads="all"
- 上传配置：protocol, s3/ftp/sftp 各自的连接参数
- 代理配置：enabled, url
- 输出模式：new_directory / overwrite
- 上次使用的输入/输出目录记忆

**Step 2: 验证配置加载/保存**

Run: `cd ImageCompression/src && python -c "from config import Config; c = Config(); c.save(); print('OK')"`
Expected: 输出 OK，在 `~/.imagecompression/` 下生成 config.json

---

### Task 3: 准备模块（重命名 + 去EXIF）

**Files:**
- Create: `ImageCompression/src/core/__init__.py`
- Create: `ImageCompression/src/core/prepare.py`

**Step 1: 实现准备模块**

功能要点：
- `scan_directory(path)`: 扫描文件夹，将文件分为图片和视频两类
  - 图片：`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`, `.tiff`
  - 视频：`.mp4`, `.mov`, `.avi`, `.mkv`, `.wmv`
- `rename_files(files, output_dir, overwrite)`: 按自然排序重命名
  - 图片: `0001.ext`, `0002.ext`, ...
  - 视频: `video001.ext`, `video002.ext`, ...
- `strip_exif(image_path)`: 用 Pillow 读取图片 → 去除 EXIF → 保存
  - 保留图片方向信息（EXIF Orientation）应用到像素后再去除
- 通过回调函数报告进度（进度百分比 + 当前处理文件名）
- 支持输出到新目录或覆盖原文件

**Step 2: 验证准备模块**

准备一个测试文件夹（3-5张测试图片），运行：
```python
from core.prepare import scan_directory, prepare_files
files = scan_directory("test_input")
prepare_files(files, output_dir="test_output", progress_callback=print)
```
Expected: 图片被重命名为 0001.xxx, 0002.xxx，EXIF 被清除

---

### Task 4: 压缩模块（AVIF/WebP/JPEG）

**Files:**
- Create: `ImageCompression/src/core/compress.py`

**Step 1: 实现压缩模块**

功能要点：
- `compress_to_avif(input_path, output_path, min_q, max_q, speed, threads)`:
  - 通过 `subprocess` 调用 `avifenc`
  - 命令：`avifenc --min {min_q} --max {max_q} --speed {speed} -j {threads} input output`
  - 捕获 stderr 获取编码进度
- `compress_to_webp(input_path, output_path, quality)`: 用 Pillow 压缩
- `compress_to_jpeg(input_path, output_path, quality)`: 用 Pillow 压缩
- `compress_directory(input_dir, output_dir, format, params, progress_callback)`:
  - 扫描输入目录的图片文件（跳过视频）
  - 根据选择的格式调用对应的压缩函数
  - 并行处理（ThreadPoolExecutor）
  - 计算压缩前后体积对比
  - 通过回调报告进度

**Step 2: 验证压缩模块**

```python
from core.compress import compress_directory
stats = compress_directory("test_input", "test_output", format="avif",
                           params={"min": 20, "max": 40, "speed": 6},
                           progress_callback=print)
print(f"原始: {stats['original_size']}MB → 压缩后: {stats['compressed_size']}MB")
```
Expected: 图片被压缩为 .avif 格式，体积显著减小

---

### Task 5: 上传模块（S3/FTP/SFTP）

**Files:**
- Create: `ImageCompression/src/core/upload.py`

**Step 1: 实现上传模块**

功能要点：
- `S3Uploader` 类：
  - 使用 boto3 上传到 S3 兼容存储
  - 配置 endpoint, bucket, access_key, secret_key, prefix
  - 支持代理（通过 botocore config 设置 proxies）
  - 上传后返回完整 URL
- `FTPUploader` 类：
  - 使用 ftplib 上传到 FTP 服务器
  - 配置 host, port, user, password, remote_dir
- `SFTPUploader` 类：
  - 使用 paramiko 上传到 SFTP 服务器
  - 配置 host, port, user, password/key, remote_dir
- `upload_directory(uploader, input_dir, progress_callback)`:
  - 遍历目录中的文件逐个上传
  - 收集上传后的 URL 列表
  - 通过回调报告进度
- 所有上传器继承统一的 `BaseUploader` 抽象类

**Step 2: 验证上传模块**

需要配置实际的 S3 连接信息后验证。可以先验证类的实例化和参数传递：
```python
from core.upload import S3Uploader
uploader = S3Uploader(endpoint="https://...", bucket="test", access_key="...", secret_key="...")
print("S3Uploader initialized OK")
```

---

### Task 6: GUI 主窗口与标签页框架

**Files:**
- Create: `ImageCompression/src/ui/__init__.py`
- Create: `ImageCompression/src/ui/main_window.py`
- Create: `ImageCompression/src/ui/widgets/__init__.py`
- Create: `ImageCompression/src/ui/widgets/progress.py`
- Create: `ImageCompression/src/ui/widgets/url_output.py`

**Step 1: 实现主窗口**

- QMainWindow + QTabWidget 布局
- 四个标签页：准备 | 压缩 | 上传 | 设置
- 底部固定：进度条 + 日志文本区域
- 窗口标题：Image Compression
- 窗口默认尺寸：900x700
- 支持文件夹拖拽（QDragEnterEvent / QDropEvent）

**Step 2: 实现进度组件 (widgets/progress.py)**

- QProgressBar + 当前文件名标签 + 统计信息（如压缩率）

**Step 3: 实现 URL 输出组件 (widgets/url_output.py)**

- QTextEdit（只读）显示 URL 列表
- "复制全部" 按钮将 URL 复制到剪贴板

**Step 4: 验证主窗口**

Run: `cd ImageCompression/src && python main.py`
Expected: 显示主窗口，四个标签页可切换，底部有进度区域

---

### Task 7: 准备页 UI

**Files:**
- Create: `ImageCompression/src/ui/prepare_tab.py`

**Step 1: 实现准备页面**

UI 元素：
- 输入目录：QLineEdit + "浏览" QPushButton（QFileDialog）
- 输出模式：QRadioButton 组（输出到新目录 / 覆盖原文件）
- 输出目录：QLineEdit + "浏览" QPushButton（仅"新目录"模式下可用）
- 复选框：☑ 重命名图片 / ☑ 重命名视频 / ☑ 清除 EXIF
- "开始处理" QPushButton
- 处理在 QThread 中异步执行，进度通过信号更新到底部进度条

**Step 2: 验证准备页**

Run: `python main.py`
Expected: 准备页 UI 正确显示，可选择目录，点击执行后图片被处理

---

### Task 8: 压缩页 UI

**Files:**
- Create: `ImageCompression/src/ui/compress_tab.py`

**Step 1: 实现压缩页面**

UI 元素：
- 输入目录：QLineEdit + "浏览"（可自动填充准备阶段的输出目录）
- 输出格式：QComboBox（AVIF / WebP / JPEG）
- AVIF 参数区（动态显示/隐藏）：
  - 质量 min: QSpinBox (0-63, 默认 20)
  - 质量 max: QSpinBox (0-63, 默认 40)
  - 编码速度: QSpinBox (0-10, 默认 6)
  - 线程数: QComboBox (全部 / 1~CPU核心数)
- WebP/JPEG 参数区：
  - 质量: QSpinBox (1-100, 默认 80)
- 输出模式：QRadioButton（新目录 / 覆盖）
- ☑ 跳过视频文件 复选框
- "开始压缩" QPushButton
- 压缩统计：原始大小 → 压缩后大小（节省百分比）

**Step 2: 验证压缩页**

Run: `python main.py`
Expected: 压缩页参数可调节，AVIF/WebP 切换时参数区动态变化，执行压缩后显示统计

---

### Task 9: 上传页 UI

**Files:**
- Create: `ImageCompression/src/ui/upload_tab.py`

**Step 1: 实现上传页面**

UI 元素：
- 协议选择：QComboBox（S3 / FTP / SFTP）
- S3 配置组（QGroupBox，动态显示）：
  - Endpoint / Bucket / Access Key / Secret Key / 远程路径前缀
- FTP 配置组：Host / Port / Username / Password / 远程目录
- SFTP 配置组：Host / Port / Username / Password or Key / 远程目录
- 代理配置：☑ 启用 + QLineEdit（如 socks5://127.0.0.1:7890）
- 上传目录：QLineEdit + "浏览"（可自动填充压缩阶段的输出目录）
- "开始上传" QPushButton
- 上传完成后自动填充 URL 输出组件

**Step 2: 验证上传页**

Run: `python main.py`
Expected: 协议切换时配置区域动态变化，可输入连接配置

---

### Task 10: 设置页 UI + 配置持久化

**Files:**
- Create: `ImageCompression/src/ui/settings_tab.py`

**Step 1: 实现设置页面**

- 所有配置参数的当前值展示
- "保存配置" / "重置默认" 按钮
- avifenc 路径配置（自动检测或手动指定）
- 启动时自动加载上次配置

**Step 2: 串联所有页面的配置读写**

- 主窗口启动时调用 `Config.load()` 填充各页面参数
- 每次执行操作后自动保存当前参数到配置

**Step 3: 验证**

Run: `python main.py`
Expected: 修改参数 → 关闭应用 → 重新打开 → 参数自动恢复

---

## 验证计划

### 手动验证流程

1. **启动应用**：`cd ImageCompression/src && python main.py`
2. **准备功能验证**：
   - 选择一个包含 5-10 张图片的测试文件夹
   - 点击"开始处理"
   - 验证：图片重命名为 0001.xxx 格式，EXIF 已清除
3. **压缩功能验证**：
   - 选择准备好的目录，设置 AVIF 格式
   - 点击"开始压缩"
   - 验证：输出 .avif 文件，进度条正常更新，压缩统计正确
4. **上传功能验证**：
   - 配置 S3 连接信息
   - 选择压缩后的目录，点击上传
   - 验证：文件上传成功，URL 列表正确显示
5. **配置持久化验证**：
   - 修改参数 → 关闭 → 重新打开
   - 验证参数自动恢复
