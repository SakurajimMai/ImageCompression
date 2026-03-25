# Phase 5 设计 — 尺寸流水线 + 性能仪表盘 + 画质评分

## 概述

为 Image Compression 添加三大高级功能：

1. **尺寸调整流水线** — 长边限制、固定尺寸、智能裁剪
2. **性能仪表盘** — CPU/内存实时监控 + 预计剩余时间
3. **SSIM + PSNR 画质评分** — 压缩后自动打分，量化"视觉无损"

## 模块一：尺寸调整流水线增强

### 现状

`resizer.py` 仅支持 `width` / `height` / `percent` 三种模式。

### 新增功能

| 模式 | 说明 | 示例 |
|---|---|---|
| `long_edge` | 限制长边，短边按比例缩 | 长边 1200px |
| `short_edge` | 限制短边 | 短边 800px |
| `fit` | 完全填入指定尺寸（缩小到刚好放进框内） | 1920×1080 |
| `fill` | 智能裁剪到指定尺寸（先缩放再居中裁剪） | 800×800 |
| `exact` | 强制拉伸到指定尺寸（不保持比例） | 640×480 |

### 技术方案

扩展 `CompressParams` 新增 `resize_width` / `resize_height` 字段；`resizer.py` 增加对应逻辑。

## 模块二：性能仪表盘

### 方案

使用 `psutil`（纯 Python）采集 CPU% / 内存占用，通过 QTimer 每秒刷新。

### UI 位置

在 compress_tab 底部 progress_widget 下方，添加一行指标：

```
CPU: 45%  |  内存: 1.2 GB  |  速度: 3.2 张/秒  |  剩余: ~2m 30s
```

### ETA 计算

```
已完成 / 总数 = 进度比
已用时间 / 进度比 - 已用时间 = 预计剩余
```

## 模块三：SSIM + PSNR 画质评分

### 方案

- **SSIM**：`skimage.metrics.structural_similarity`（scikit-image），0-1 分
- **PSNR**：`skimage.metrics.peak_signal_noise_ratio`，dB 值

### 评级标准

| SSIM | PSNR (dB) | 评级 |
|---|---|---|
| ≥ 0.98 | ≥ 45 | ⭐ 视觉无损 |
| ≥ 0.95 | ≥ 38 | ✅ 优秀 |
| ≥ 0.90 | ≥ 32 | 🟡 良好 |
| < 0.90 | < 32 | 🔴 较差 |

### 集成点

- `CompressResult` 新增 `ssim` / `psnr` / `quality_grade` 字段
- `pipeline.py` 压缩后对比原图与输出计算分数
- compress_tab 统计区显示平均 SSIM/PSNR
- preview_dialog 每张图显示评分

## 文件变更清单

| 文件 | 变更 |
|---|---|
| `engine/resizer.py` | 新增 long_edge / short_edge / fit / fill / exact 模式 |
| `engine/formats/base.py` | CompressResult 新增 ssim / psnr / quality_grade |
| `engine/quality.py` | [NEW] SSIM + PSNR 计算模块 |
| `engine/pipeline.py` | 压缩后调用画质评分 |
| `ui/compress_tab.py` | 新增缩放模式 + 性能仪表盘 |
| `ui/widgets/perf_monitor.py` | [NEW] 性能指标组件 (psutil) |
| `requirements.txt` | + psutil, scikit-image |
