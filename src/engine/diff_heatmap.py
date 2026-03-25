"""
差异热力图 — 压缩前后像素差异可视化

生成一张热力图，高亮显示压缩后图片与原图的差异区域。
红色=差异大，蓝色=差异小，黑色=无差异。
"""
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image


def generate_diff_heatmap(
    original_path: str | Path,
    compressed_path: str | Path,
    amplify: int = 10,
) -> Optional[Image.Image]:
    """
    生成差异热力图

    Args:
        original_path: 原图路径
        compressed_path: 压缩后路径
        amplify: 差异放大倍数 (默认 10x)

    Returns:
        PIL Image (RGB 热力图) 或 None
    """
    try:
        with Image.open(original_path) as orig, Image.open(compressed_path) as comp:
            orig_rgb = orig.convert("RGB")
            comp_rgb = comp.convert("RGB")

            # 尺寸对齐
            if orig_rgb.size != comp_rgb.size:
                comp_rgb = comp_rgb.resize(orig_rgb.size, Image.Resampling.LANCZOS)

            arr1 = np.array(orig_rgb, dtype=np.float32)
            arr2 = np.array(comp_rgb, dtype=np.float32)

            # 计算逐像素差异（L2 范数）
            diff = np.sqrt(np.sum((arr1 - arr2) ** 2, axis=2))

            # 归一化到 0-255 并放大
            diff_amplified = np.clip(diff * amplify, 0, 255).astype(np.uint8)

            # 应用颜色映射（冷暖色调）
            heatmap = _apply_colormap(diff_amplified)

            return Image.fromarray(heatmap)

    except Exception:
        return None


def _apply_colormap(gray: np.ndarray) -> np.ndarray:
    """
    将灰度差异图转换为冷暖色调热力图

    0 → 黑色 (无差异)
    低 → 蓝色/青色
    中 → 黄色/橙色
    高 → 红色/白色
    """
    h, w = gray.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)

    # 归一化到 0-1
    normalized = gray.astype(np.float32) / 255.0

    # R 通道：中高差异区域
    rgb[:, :, 0] = np.clip(normalized * 3.0, 0, 1) * 255

    # G 通道：中等差异区域（峰值在中间）
    rgb[:, :, 1] = np.clip(
        np.where(normalized < 0.5,
                 normalized * 2.0,
                 (1.0 - normalized) * 2.0),
        0, 1
    ) * 255

    # B 通道：低差异区域
    rgb[:, :, 2] = np.clip((1.0 - normalized * 2.0), 0, 1) * 255

    # 无差异区域保持黑色
    mask = gray < 3
    rgb[mask] = 0

    return rgb


def generate_diff_overlay(
    original_path: str | Path,
    compressed_path: str | Path,
    opacity: float = 0.5,
    amplify: int = 10,
) -> Optional[Image.Image]:
    """
    生成差异叠加图 — 将热力图半透明叠加在原图上

    Args:
        original_path: 原图路径
        compressed_path: 压缩后路径
        opacity: 热力图透明度 (0-1)
        amplify: 差异放大倍数

    Returns:
        PIL Image (叠加后) 或 None
    """
    try:
        heatmap = generate_diff_heatmap(original_path, compressed_path, amplify)
        if heatmap is None:
            return None

        with Image.open(original_path) as orig:
            orig_rgb = orig.convert("RGB")
            if orig_rgb.size != heatmap.size:
                heatmap = heatmap.resize(orig_rgb.size, Image.Resampling.LANCZOS)

            return Image.blend(orig_rgb, heatmap, opacity)

    except Exception:
        return None
