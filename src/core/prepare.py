"""
准备模块 — 扫描文件夹、重命名文件、清除 EXIF
"""
import shutil
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass

from PIL import Image, ExifTags

from engine.scanner import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, ScanResult


@dataclass
class PrepareResult:
    """准备处理结果"""
    renamed_images: int
    renamed_videos: int
    exif_stripped: int
    output_dir: str


def strip_exif(image_path: Path, output_path: Optional[Path] = None):
    """清除图片的 EXIF 信息，保留方向信息应用到像素"""
    if output_path is None:
        output_path = image_path

    try:
        with Image.open(image_path) as img:
            # 处理 EXIF 方向信息 —— 先应用旋转再去除 EXIF
            try:
                exif = img.getexif()
                orientation_key = None
                for key, val in ExifTags.TAGS.items():
                    if val == "Orientation":
                        orientation_key = key
                        break

                if orientation_key and orientation_key in exif:
                    orientation = exif[orientation_key]
                    rotate_map = {
                        3: 180,
                        6: 270,
                        8: 90,
                    }
                    if orientation in rotate_map:
                        img = img.rotate(rotate_map[orientation], expand=True)
            except (AttributeError, KeyError):
                pass

            # 重新保存（不带 EXIF）
            save_kwargs = {}
            fmt = img.format or image_path.suffix.lstrip(".").upper()
            if fmt in ("JPG", "JPEG"):
                fmt = "JPEG"
                save_kwargs["quality"] = 95
                save_kwargs["subsampling"] = 0
            elif fmt == "PNG":
                pass  # PNG 默认设置即可
            elif fmt == "WEBP":
                save_kwargs["quality"] = 95

            # 转换为 RGB（如果是 RGBA 且保存为 JPEG）
            if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.save(output_path, format=fmt, **save_kwargs)
    except Exception as e:
        # 无法处理的文件直接复制
        if output_path != image_path:
            shutil.copy2(image_path, output_path)
        raise e


def prepare_files(
    scan_result: ScanResult,
    output_dir: str | Path,
    rename_images: bool = True,
    rename_videos: bool = True,
    do_strip_exif: bool = True,
    overwrite: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> PrepareResult:
    """
    处理文件：重命名 + 清除 EXIF

    递归模式下保留子目录结构，每个子目录内独立编号。
    """
    output_path = Path(output_dir)
    total_files = len(scan_result.images) + len(scan_result.videos)
    current = 0
    renamed_images = 0
    renamed_videos = 0
    exif_stripped = 0

    if not overwrite:
        output_path.mkdir(parents=True, exist_ok=True)

    base_dir = getattr(scan_result, 'base_dir', None)

    # ── 按子目录分组，每组独立编号 ──
    def _group_by_parent(files: list[Path]) -> dict[Path, list[Path]]:
        groups: dict[Path, list[Path]] = {}
        for f in files:
            groups.setdefault(f.parent, []).append(f)
        return groups

    # 处理图片
    img_groups = _group_by_parent(scan_result.images)
    for parent_dir, files in img_groups.items():
        # 计算相对路径
        if base_dir and parent_dir != base_dir:
            try:
                rel = parent_dir.relative_to(base_dir)
            except ValueError:
                rel = Path(".")
        else:
            rel = Path(".")

        for i, img_file in enumerate(files):
            if rename_images:
                new_name = f"{i + 1:04d}{img_file.suffix.lower()}"
            else:
                new_name = img_file.name

            if overwrite:
                dest = img_file.parent / new_name
            else:
                dest_dir = output_path / rel if rel != Path(".") else output_path
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / new_name

            current += 1
            if progress_callback:
                progress_callback(current, total_files, f"处理图片: {img_file.name} → {new_name}")

            if do_strip_exif:
                try:
                    strip_exif(img_file, dest)
                    exif_stripped += 1
                except Exception:
                    if not overwrite or dest != img_file:
                        shutil.copy2(img_file, dest)
            else:
                if not overwrite or dest != img_file:
                    shutil.copy2(img_file, dest)

            if rename_images:
                renamed_images += 1

    # 处理视频
    vid_groups = _group_by_parent(scan_result.videos)
    for parent_dir, files in vid_groups.items():
        if base_dir and parent_dir != base_dir:
            try:
                rel = parent_dir.relative_to(base_dir)
            except ValueError:
                rel = Path(".")
        else:
            rel = Path(".")

        for i, vid_file in enumerate(files):
            if rename_videos:
                new_name = f"video{i + 1:03d}{vid_file.suffix.lower()}"
            else:
                new_name = vid_file.name

            if overwrite:
                dest = vid_file.parent / new_name
            else:
                dest_dir = output_path / rel if rel != Path(".") else output_path
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / new_name

            current += 1
            if progress_callback:
                progress_callback(current, total_files, f"处理视频: {vid_file.name} → {new_name}")

            if not overwrite or dest != vid_file:
                shutil.copy2(vid_file, dest)

            if rename_videos:
                renamed_videos += 1

    return PrepareResult(
        renamed_images=renamed_images,
        renamed_videos=renamed_videos,
        exif_stripped=exif_stripped,
        output_dir=str(output_path),
    )
