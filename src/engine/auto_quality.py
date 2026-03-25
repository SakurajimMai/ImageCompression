"""
自动质量二分法 — 二分搜索最优质量参数

原理：
  给定目标 SSIM（如 0.95），通过二分搜索找到满足该 SSIM 的最低质量参数，
  从而实现"视觉无损但文件最小"的效果。

用法：
  result = auto_find_quality(
      input_path="photo.jpg",
      format_name="avif",
      target_ssim=0.95,
  )
  print(f"最优质量: {result['quality']}, SSIM: {result['ssim']}")
"""
import tempfile
from pathlib import Path
from typing import Optional

from engine.formats.base import CompressParams
from engine.formats.registry import get_handler
from engine.quality import evaluate_quality


def auto_find_quality(
    input_path: str | Path,
    format_name: str = "avif",
    target_ssim: float = 0.95,
    min_quality: int = 10,
    max_quality: int = 95,
    max_iterations: int = 8,
    extra_params: Optional[dict] = None,
    progress_callback=None,
) -> dict:
    """
    二分搜索最优质量参数

    Args:
        input_path: 输入图片路径
        format_name: 输出格式
        target_ssim: 目标 SSIM (0-1)
        min_quality: 搜索下界
        max_quality: 搜索上界
        max_iterations: 最大迭代次数
        extra_params: 额外压缩参数
        progress_callback: 进度回调 (iteration, quality, ssim, file_size)

    Returns:
        {
            "quality": int,       # 最优质量参数
            "ssim": float,        # 对应 SSIM
            "psnr": float,        # 对应 PSNR
            "grade": str,         # 评级
            "file_size": int,     # 压缩后文件大小
            "iterations": int,    # 搜索迭代次数
            "history": list,      # 搜索历史
        }
    """
    input_path = Path(input_path)
    handler = get_handler(format_name)

    history = []
    best_result = None

    lo, hi = min_quality, max_quality

    for iteration in range(max_iterations):
        mid = (lo + hi) // 2

        # 构建参数
        params = CompressParams(quality=mid, speed=6)
        if extra_params:
            params.extra = extra_params

        # 使用临时文件压缩
        ext = handler.default_extension()
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            result = handler.compress(input_path, tmp_path, params)

            if not result.success:
                # 压缩失败，缩小范围
                hi = mid - 1
                continue

            # 评估画质
            q = evaluate_quality(input_path, tmp_path)
            if q is None:
                hi = mid - 1
                continue

            ssim = q["ssim"]
            psnr = q["psnr"]
            file_size = tmp_path.stat().st_size

            record = {
                "iteration": iteration + 1,
                "quality": mid,
                "ssim": ssim,
                "psnr": psnr,
                "file_size": file_size,
            }
            history.append(record)

            if progress_callback:
                progress_callback(iteration + 1, mid, ssim, file_size)

            # 二分逻辑
            if ssim >= target_ssim:
                best_result = record
                hi = mid - 1  # 尝试更低质量
            else:
                lo = mid + 1  # 需要更高质量

        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass

        # 收敛
        if lo > hi:
            break

    # 如果没有找到满足条件的，使用历史中 SSIM 最接近目标的
    if best_result is None and history:
        best_result = min(history, key=lambda r: abs(r["ssim"] - target_ssim))

    if best_result is None:
        return {
            "quality": max_quality,
            "ssim": 0,
            "psnr": 0,
            "grade": "未知",
            "file_size": 0,
            "iterations": len(history),
            "history": history,
        }

    from engine.quality import get_quality_grade
    grade = get_quality_grade(best_result["ssim"], best_result["psnr"])

    return {
        "quality": best_result["quality"],
        "ssim": best_result["ssim"],
        "psnr": best_result["psnr"],
        "grade": grade,
        "file_size": best_result["file_size"],
        "iterations": len(history),
        "history": history,
    }
