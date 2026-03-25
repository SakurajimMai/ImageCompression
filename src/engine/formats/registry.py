"""
格式注册表 — 插件发现与管理
"""
from engine.formats.base import FormatHandler

_handlers: dict[str, FormatHandler] = {}


def register_handler(handler: FormatHandler):
    """注册一个格式处理器"""
    _handlers[handler.name] = handler


def get_handler(name: str) -> FormatHandler:
    """获取指定格式的处理器"""
    name = name.lower()
    if name not in _handlers:
        available = ", ".join(_handlers.keys())
        raise ValueError(f"未知格式 '{name}'，可用格式: {available}")
    return _handlers[name]


def list_handlers() -> list[FormatHandler]:
    """列出所有已注册的格式处理器"""
    return list(_handlers.values())


def _auto_discover():
    """自动导入并注册内置格式处理器"""
    # 延迟导入，避免循环依赖
    from engine.formats import avif, webp, jpeg  # noqa: F401


# 模块加载时自动发现
_auto_discover()
