# CLI API 参考

> Image Compression CLI 完整命令参考

## 命令概览

```
python cli.py [OPTIONS] COMMAND [ARGS]
```

| 命令 | 说明 |
|---|---|
| `compress` | 压缩图片目录 |
| `info` | 查看图片信息 |
| `scan` | 扫描目录统计 |
| `presets` | 列出可用预设 |

---

## compress

压缩图片目录。

```
python cli.py compress [INPUT_DIR] [OPTIONS]
```

### 参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `INPUT_DIR` | Path | 输入目录（可选，配合 --stdin 使用） |

### 选项

#### 基本选项

| 选项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `-f, --format` | Choice | `avif` | 输出格式 (`avif` / `webp` / `jpeg`) |
| `-o, --output` | Path | `<input>_<fmt>` | 输出目录 |
| `-q, --quality` | Int 0-100 | `55` | 压缩质量 |
| `--preset` | Choice | — | 使用预设模板 |
| `--overwrite` | Flag | — | 覆盖原文件 |
| `--quiet` | Flag | — | 安静模式 |

#### AVIF 专用选项

| 选项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `-s, --speed` | Int 0-10 | `6` | 编码速度 (0=最慢最好, 10=最快) |
| `--yuv` | Choice | `420` | YUV 采样 (`420` / `422` / `444`) |
| `--depth` | Choice | `8` | 位深度 (`8` / `10` / `12`) |
| `--lossless` | Flag | — | 无损压缩 |
| `--progressive` | Flag | — | 渐进式输出 (需 libavif 1.1+) |

#### 批量选项

| 选项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `-r, --recursive` | Flag | — | 递归处理子目录 |
| `-j, --workers` | Int | `1` | 并行线程数 |
| `--conflict` | Choice | `overwrite` | 同名策略 (`overwrite` / `skip` / `rename`) |
| `--retries` | Int | `1` | 失败重试次数 |

#### 缩放选项

| 选项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `--resize` | String | — | 缩放 (`w800` / `h600` / `50%`) |

#### 元数据选项

| 选项 | 默认值 | 说明 |
|---|---|---|
| `--strip-exif / --keep-exif` | strip | 清除/保留 EXIF |
| `--keep-icc / --strip-icc` | keep | 保留/清除 ICC Profile |
| `--strip-xmp / --keep-xmp` | strip | 清除/保留 XMP |

#### 输入选项

| 选项 | 说明 |
|---|---|
| `--stdin` | 从 stdin 读取输入目录路径 |

### 示例

```bash
# 基本压缩
python cli.py compress ./photos -f avif -q 55 -o ./output

# 使用预设
python cli.py compress ./photos --preset web

# 递归 + 4 线程并行
python cli.py compress ./photos -f webp -r -j 4

# 无损 HDR
python cli.py compress ./photos --lossless --depth 10 --yuv 444

# 缩放 + 清除元数据
python cli.py compress ./photos --resize w800 --strip-exif

# 管道输入
echo "C:/photos" | python cli.py compress --stdin -f avif

# 跳过已存在文件
python cli.py compress ./photos -o ./out --conflict skip

# 覆盖原文件
python cli.py compress ./photos --overwrite --preset max_compress
```

---

## info

查看单个图片的详细信息。

```
python cli.py info IMAGE_PATH
```

### 输出

```
文件: photo.jpg
大小: 2.3 MB
尺寸: 4032 × 3024
格式: JPEG
透明: 否
EXIF: 有 (42 字段)
ICC:  有
XMP:  无
```

---

## scan

扫描目录统计文件数量和大小。

```
python cli.py scan INPUT_DIR [OPTIONS]
```

| 选项 | 说明 |
|---|---|
| `-r, --recursive` | 递归扫描子目录 |

### 输出

```
目录: ./photos
图片: 128 张
视频: 3 个
总大小: 450.2 MB
子目录: 5 个
```

---

## presets

列出所有可用预设模板。

```
python cli.py presets
```

### 预设表

| 名称 | 显示名 | 质量 | 速度 | YUV | 位深 | 说明 |
|---|---|---|---|---|---|---|
| `web` | 网页 | 55 | 6 | 420 | 8 | 网页展示，平衡质量与体积 |
| `mobile` | 移动端 | 60 | 6 | 420 | 8 | 移动端优化 |
| `lossless` | 无损 | 100 | 4 | 444 | 10 | 完全无损压缩 |
| `max_compress` | 极致压缩 | 30 | 4 | 420 | 8 | 最小文件体积 |
| `hdr` | HDR | 65 | 4 | 444 | 10 | HDR / Gain Map 模式 |

---

## 退出码

| 码 | 含义 |
|---|---|
| `0` | 成功 |
| `1` | 参数错误或运行失败 |

## Engine Python API

核心函数可直接在 Python 脚本中使用：

```python
from engine.formats.base import CompressParams
from engine.pipeline import compress_batch
from engine.presets import get_preset

# 使用预设
params = get_preset("web")

# 批量压缩
stats = compress_batch(
    input_dir="./photos",
    output_dir="./output",
    format_name="avif",
    params=params,
    recursive=True,
    max_workers=4,
)

print(f"压缩了 {stats.compressed_files} 个文件")
print(f"节省 {stats.saved_percent:.1f}%")
```
