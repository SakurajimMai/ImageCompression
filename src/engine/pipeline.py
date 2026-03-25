"""
处理管线 — 批量压缩的核心调度器

支持：
- 递归目录（保持子目录结构）
- 并行处理
- 进度回调 + 实时速度
- 跳过/覆盖/重命名策略
- 错误处理（跳过损坏 + 自动重试）
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

from engine.formats.base import CompressParams, CompressResult
from engine.formats.registry import get_handler
from engine.scanner import scan_directory, IMAGE_EXTENSIONS
from engine.stats import BatchStats


def compress_batch(
    input_dir: str | Path,
    output_dir: str | Path,
    format_name: str = "avif",
    params: Optional[CompressParams] = None,
    overwrite: bool = False,
    recursive: bool = False,
    max_workers: int = 1,
    conflict_strategy: str = "overwrite",  # overwrite / skip / rename
    max_retries: int = 0,
    progress_callback: Optional[Callable[[int, int, str, float], None]] = None,
) -> BatchStats:
    """
    批量压缩目录中的图片

    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        format_name: 输出格式名 (avif/webp/jpeg)
        params: 压缩参数
        overwrite: 覆盖原文件（output_dir 被忽略）
        recursive: 递归子目录
        max_workers: 并行线程数
        conflict_strategy: 同名文件策略 (overwrite/skip/rename)
        max_retries: 最大重试次数
        progress_callback: 进度回调 (current, total, message, speed_fps)
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir) if not overwrite else input_path
    params = params or CompressParams()

    handler = get_handler(format_name)
    target_ext = handler.default_extension()

    if not overwrite:
        output_path.mkdir(parents=True, exist_ok=True)

    # 收集待处理文件
    scan = scan_directory(input_path, recursive=recursive)
    image_files = scan.images
    total = len(image_files)

    stats = BatchStats(output_dir=str(output_path))
    batch_start = time.time()

    def _process_one(img_file: Path, index: int) -> CompressResult:
        """处理单个文件"""
        # 计算输出路径（保持子目录结构）
        if recursive and img_file.parent != input_path:
            rel = img_file.relative_to(input_path)
            out_file = output_path / rel.parent / (rel.stem + target_ext)
        else:
            out_file = output_path / (img_file.stem + target_ext)

        # 同名文件策略
        if out_file.exists():
            if conflict_strategy == "skip":
                return CompressResult(
                    success=True,
                    input_path=str(img_file),
                    output_path=str(out_file),
                    original_size=img_file.stat().st_size,
                    compressed_size=out_file.stat().st_size,
                    error="skipped",
                )
            elif conflict_strategy == "rename":
                counter = 1
                stem = out_file.stem
                while out_file.exists():
                    out_file = out_file.parent / f"{stem}_{counter}{target_ext}"
                    counter += 1

        # 压缩（含重试）
        last_result = None
        for attempt in range(max_retries + 1):
            result = handler.compress(img_file, out_file, params)
            last_result = result
            if result.success:
                break

        # 覆盖模式下：如果压缩成功且扩展名变了（如 jpg→avif），删除原始文件
        if overwrite and last_result and last_result.success:
            if img_file.suffix.lower() != target_ext and out_file.exists():
                try:
                    img_file.unlink()
                except OSError:
                    pass

        return last_result

    # 执行压缩
    if max_workers <= 1 or format_name == "avif":
        # AVIF 使用 avifenc 自带多线程，外部串行即可
        for i, img_file in enumerate(image_files):
            result = _process_one(img_file, i)

            if result.error == "skipped":
                stats.skipped_files += 1
                stats.total_files += 1
            else:
                stats.add_result(result)

            # 进度回调
            if progress_callback:
                elapsed = time.time() - batch_start
                speed = (i + 1) / elapsed if elapsed > 0 else 0
                progress_callback(
                    i + 1, total,
                    f"压缩: {img_file.name}",
                    speed,
                )
    else:
        # WebP/JPEG 可并行处理
        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_process_one, f, i): (i, f)
                for i, f in enumerate(image_files)
            }
            for future in as_completed(futures):
                i, img_file = futures[future]
                result = future.result()

                if result.error == "skipped":
                    stats.skipped_files += 1
                    stats.total_files += 1
                else:
                    stats.add_result(result)

                completed += 1
                if progress_callback:
                    elapsed = time.time() - batch_start
                    speed = completed / elapsed if elapsed > 0 else 0
                    progress_callback(
                        completed, total,
                        f"压缩: {img_file.name}",
                        speed,
                    )

    # 使用墙钟时间覆盖累加时间（并行模式下累加值 > 实际耗时）
    stats.total_elapsed = time.time() - batch_start
    return stats
