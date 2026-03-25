"""
文件扫描器 — 递归扫描目录，分类文件
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import re


# 支持的输入格式
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif",
    ".tiff", ".tif", ".heic", ".heif", ".avif",
}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".y4m"}


@dataclass
class ScanResult:
    """扫描结果"""
    base_dir: Path
    images: list[Path] = field(default_factory=list)
    videos: list[Path] = field(default_factory=list)
    others: list[Path] = field(default_factory=list)
    total_size: int = 0
    subdirs: int = 0

    @property
    def image_count(self) -> int:
        return len(self.images)

    @property
    def video_count(self) -> int:
        return len(self.videos)

    @property
    def total_size_mb(self) -> float:
        return self.total_size / (1024 * 1024)


def scan_directory(
    path: str | Path,
    recursive: bool = False,
    include_videos: bool = False,
) -> ScanResult:
    """
    扫描目录，将文件分类

    Args:
        path: 目标目录
        recursive: 是否递归子目录
        include_videos: 是否包含视频文件
    """
    path = Path(path)
    result = ScanResult(base_dir=path)
    seen_dirs = set()

    if recursive:
        all_files = sorted(path.rglob("*"))
    else:
        all_files = sorted(path.iterdir())

    for f in all_files:
        if not f.is_file():
            continue

        ext = f.suffix.lower()

        try:
            size = f.stat().st_size
        except OSError:
            continue  # 跳过无法访问的文件

        result.total_size += size

        # 记录子目录数量
        if f.parent != path:
            seen_dirs.add(f.parent)

        if ext in IMAGE_EXTENSIONS:
            result.images.append(f)
        elif ext in VIDEO_EXTENSIONS:
            result.videos.append(f)
        else:
            result.others.append(f)

    result.subdirs = len(seen_dirs)

    # 自然排序：“01 (2)” 排在 “01 (10)” 前面
    def _nat_key(p: Path):
        return [int(s) if s.isdigit() else s.lower()
                for s in re.split(r'(\d+)', p.name)]

    result.images.sort(key=_nat_key)
    result.videos.sort(key=_nat_key)

    return result
