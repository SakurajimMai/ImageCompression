"""
画质评分模块 — SSIM + PSNR

SSIM (Structural Similarity)：0-1 分，越接近 1 越好
PSNR (Peak Signal-to-Noise Ratio)：dB 值，越高越好

评级标准:
  ≥ 0.98 / ≥ 45dB  →  ⭐ 视觉无损
  ≥ 0.95 / ≥ 38dB  →  ✅ 优秀
  ≥ 0.90 / ≥ 32dB  →  🟡 良好
  < 0.90 / < 32dB  →  🔴 较差
"""
from pathlib import Path
from typing import Optional

from PIL import Image
import numpy as np


def compute_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """计算 SSIM（不依赖 skimage 的简化版本，兼容任意环境）"""
    try:
        from skimage.metrics import structural_similarity
        # 自动检测多通道
        multichannel = img1.ndim == 3
        return structural_similarity(
            img1, img2,
            channel_axis=2 if multichannel else None,
            data_range=255,
        )
    except ImportError:
        # 回退：简化 SSIM 实现
        return _simple_ssim(img1.astype(np.float64), img2.astype(np.float64))


def _simple_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """简化 SSIM 实现（不依赖 skimage）"""
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    mu1 = img1.mean()
    mu2 = img2.mean()
    sigma1_sq = img1.var()
    sigma2_sq = img2.var()
    sigma12 = ((img1 - mu1) * (img2 - mu2)).mean()

    ssim = ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / (
        (mu1 ** 2 + mu2 ** 2 + C1) * (sigma1_sq + sigma2_sq + C2)
    )
    return float(ssim)


def compute_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    """计算 PSNR (dB)"""
    mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return float(10 * np.log10(255.0 ** 2 / mse))


def get_quality_grade(ssim: float, psnr: float) -> str:
    """根据 SSIM 和 PSNR 返回评级"""
    if ssim >= 0.98 and psnr >= 45:
        return "⭐ 视觉无损"
    elif ssim >= 0.95 and psnr >= 38:
        return "✅ 优秀"
    elif ssim >= 0.90 and psnr >= 32:
        return "🟡 良好"
    else:
        return "🔴 较差"


def evaluate_quality(
    original_path: Path | str,
    compressed_path: Path | str,
) -> dict:
    """
    对比原图和压缩后图片，计算画质评分

    Returns:
        {"ssim": float, "psnr": float, "grade": str}
        或 None（如果无法计算）
    """
    try:
        with Image.open(original_path) as orig, Image.open(compressed_path) as comp:
            # 统一为 RGB，忽略 alpha
            orig_rgb = orig.convert("RGB")
            comp_rgb = comp.convert("RGB")

            # 尺寸对齐（压缩后可能被缩放）
            if orig_rgb.size != comp_rgb.size:
                comp_rgb = comp_rgb.resize(orig_rgb.size, Image.Resampling.LANCZOS)

            arr1 = np.array(orig_rgb)
            arr2 = np.array(comp_rgb)

            ssim = compute_ssim(arr1, arr2)
            psnr = compute_psnr(arr1, arr2)
            grade = get_quality_grade(ssim, psnr)

            return {"ssim": round(ssim, 4), "psnr": round(psnr, 2), "grade": grade}

    except Exception:
        return None
