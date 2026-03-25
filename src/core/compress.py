"""
压缩工具函数 — avifenc 可用性检查
"""
import subprocess


def check_avifenc(avifenc_path: str = "avifenc") -> tuple[bool, str]:
    """检查 avifenc 是否可用，返回 (可用?, 版本信息)"""
    try:
        result = subprocess.run(
            [avifenc_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version = result.stdout.strip() or result.stderr.strip()
        return True, version
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "avifenc 未找到，请先安装 libavif"
