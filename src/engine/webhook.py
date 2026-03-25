"""
Webhook 回调 — 压缩完成后发送 HTTP 通知

支持:
  - 自定义 URL
  - JSON payload（压缩统计摘要）
  - 可选 Authorization Header
"""
import json
import time
import urllib.request
import urllib.error
from typing import Optional

from engine.stats import BatchStats


def send_webhook(
    url: str,
    stats: BatchStats,
    format_name: str = "",
    auth_header: str = "",
    timeout: int = 10,
) -> dict:
    """
    发送压缩完成 Webhook

    Args:
        url: Webhook URL
        stats: 压缩统计
        format_name: 使用的格式
        auth_header: Authorization header (可选)
        timeout: 超时秒数

    Returns:
        {"success": bool, "status_code": int, "message": str}
    """
    if not url:
        return {"success": False, "status_code": 0, "message": "URL 为空"}

    # 构建 payload
    payload = {
        "event": "compression_complete",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "format": format_name,
            "total_files": stats.total_files,
            "compressed": stats.compressed_files,
            "failed": stats.failed_files,
            "skipped": stats.skipped_files,
            "original_size_mb": round(stats.original_size_mb, 2),
            "compressed_size_mb": round(stats.compressed_size_mb, 2),
            "saved_percent": round(stats.saved_percent, 1),
            "elapsed_seconds": round(stats.total_elapsed, 1),
            "output_dir": stats.output_dir,
        },
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ImageCompression/2.0",
    }
    if auth_header:
        headers["Authorization"] = auth_header

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {
                "success": True,
                "status_code": resp.status,
                "message": f"HTTP {resp.status}",
            }
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "status_code": e.code,
            "message": f"HTTP {e.code}: {e.reason}",
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "message": str(e),
        }
