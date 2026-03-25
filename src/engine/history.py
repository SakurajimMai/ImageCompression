"""
压缩历史记录 — JSON 持久化

每次批量压缩完成后自动记录：
- 时间戳
- 输入/输出目录
- 格式/参数
- 文件数/压缩率
- 每文件详情（可选）
"""
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from engine.stats import BatchStats

# 默认历史文件位置
DEFAULT_HISTORY_DIR = Path.home() / ".imagecompression"
DEFAULT_HISTORY_FILE = DEFAULT_HISTORY_DIR / "history.json"
MAX_HISTORY_ITEMS = 500  # 最多保留 500 条


def _ensure_dir():
    DEFAULT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def save_history_entry(
    stats: BatchStats,
    format_name: str = "",
    preset_name: str = "",
    quality: int = 0,
    input_dir: str = "",
) -> dict:
    """
    保存一次压缩记录

    Returns:
        保存的记录 dict
    """
    _ensure_dir()

    # 构建记录
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": int(time.time()),
        "input_dir": input_dir,
        "output_dir": stats.output_dir,
        "format": format_name,
        "preset": preset_name,
        "quality": quality,
        "total_files": stats.total_files,
        "compressed_files": stats.compressed_files,
        "failed_files": stats.failed_files,
        "skipped_files": stats.skipped_files,
        "original_size_mb": round(stats.original_size_mb, 2),
        "compressed_size_mb": round(stats.compressed_size_mb, 2),
        "saved_percent": round(stats.saved_percent, 1),
        "elapsed_seconds": round(stats.total_elapsed, 1),
    }

    # 读取现有历史
    history = load_history()
    history.insert(0, entry)

    # 限制数量
    if len(history) > MAX_HISTORY_ITEMS:
        history = history[:MAX_HISTORY_ITEMS]

    # 写入
    with open(DEFAULT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return entry


def load_history(limit: int = 0) -> list[dict]:
    """加载历史记录"""
    if not DEFAULT_HISTORY_FILE.exists():
        return []

    try:
        with open(DEFAULT_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if limit > 0:
            return data[:limit]
        return data
    except (json.JSONDecodeError, IOError):
        return []


def clear_history():
    """清空历史记录"""
    if DEFAULT_HISTORY_FILE.exists():
        DEFAULT_HISTORY_FILE.unlink()


def get_stats_summary() -> dict:
    """获取历史统计汇总"""
    history = load_history()
    if not history:
        return {
            "total_sessions": 0,
            "total_files": 0,
            "total_saved_mb": 0,
            "avg_saved_percent": 0,
            "format_distribution": {},
        }

    total_files = sum(h.get("total_files", 0) for h in history)
    total_original = sum(h.get("original_size_mb", 0) for h in history)
    total_compressed = sum(h.get("compressed_size_mb", 0) for h in history)
    saved_pcts = [h.get("saved_percent", 0) for h in history if h.get("saved_percent", 0) > 0]

    # 格式分布
    fmt_dist = {}
    for h in history:
        fmt = h.get("format", "unknown")
        fmt_dist[fmt] = fmt_dist.get(fmt, 0) + 1

    return {
        "total_sessions": len(history),
        "total_files": total_files,
        "total_saved_mb": round(total_original - total_compressed, 1),
        "avg_saved_percent": round(sum(saved_pcts) / len(saved_pcts), 1) if saved_pcts else 0,
        "format_distribution": fmt_dist,
    }
