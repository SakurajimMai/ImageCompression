"""
预设模板 — 一键参数配置
"""
from engine.formats.base import CompressParams


# 预设定义
PRESETS: dict[str, dict] = {
    "web": {
        "display_name": "Web 优化",
        "description": "适合网页展示，平衡质量与大小 (quality=55)",
        "params": {
            "quality": 55,
            "speed": 6,
            "lossless": False,
            "extra": {"yuv": "420", "depth": 8},
        },
    },
    "mobile": {
        "display_name": "手机优化",
        "description": "针对移动端，稍高质量 (quality=60)",
        "params": {
            "quality": 60,
            "speed": 6,
            "lossless": False,
            "extra": {"yuv": "420", "depth": 8},
        },
    },
    "lossless": {
        "display_name": "无损压缩",
        "description": "完全无损，文件较大",
        "params": {
            "quality": 100,
            "speed": 4,
            "lossless": True,
            "extra": {"yuv": "444", "depth": 10},
        },
    },
    "max_compress": {
        "display_name": "极致压缩",
        "description": "最小文件体积，牺牲质量 (quality=30)",
        "params": {
            "quality": 30,
            "speed": 4,
            "lossless": False,
            "extra": {"yuv": "420", "depth": 8},
        },
    },
    "hdr": {
        "display_name": "HDR 模式",
        "description": "保留 HDR 信息，10位色深",
        "params": {
            "quality": 65,
            "speed": 4,
            "lossless": False,
            "extra": {"yuv": "444", "depth": 10},
        },
    },
}


def get_preset(name: str) -> CompressParams:
    """获取预设参数"""
    name = name.lower()
    if name not in PRESETS:
        available = ", ".join(PRESETS.keys())
        raise ValueError(f"未知预设 '{name}'，可用: {available}")

    cfg = PRESETS[name]["params"]
    return CompressParams(
        quality=cfg["quality"],
        speed=cfg["speed"],
        lossless=cfg["lossless"],
        extra=dict(cfg.get("extra", {})),
    )


def list_presets() -> list[dict]:
    """列出所有预设"""
    return [
        {"name": k, "display_name": v["display_name"], "description": v["description"]}
        for k, v in PRESETS.items()
    ]
