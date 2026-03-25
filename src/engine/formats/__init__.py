"""
格式处理器插件包

使用方法:
    from engine.formats.registry import get_handler, list_handlers
    handler = get_handler("avif")
    result = handler.compress(input_path, output_path, params)
"""
from engine.formats.registry import get_handler, list_handlers, register_handler

__all__ = ["get_handler", "list_handlers", "register_handler"]
