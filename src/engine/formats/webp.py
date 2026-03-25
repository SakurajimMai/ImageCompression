"""
WebP 格式处理器 — 通过 Pillow 实现
"""
import time
from pathlib import Path
from typing import Optional

from PIL import Image

from engine.formats.base import (
    FormatHandler, CompressResult, CompressParams, ImageInfo,
)
from engine.formats.registry import register_handler
from engine.resizer import resize_image


class WebPHandler(FormatHandler):
    """WebP 格式处理器"""

    @property
    def name(self) -> str:
        return "webp"

    @property
    def display_name(self) -> str:
        return "WebP"

    @property
    def extensions(self) -> list[str]:
        return [".webp"]

    @property
    def supports_lossless(self) -> bool:
        return True

    @property
    def supports_alpha(self) -> bool:
        return True

    def compress(
        self,
        input_path: Path,
        output_path: Path,
        params: CompressParams,
    ) -> CompressResult:
        start_time = time.time()
        original_size = input_path.stat().st_size

        try:
            with Image.open(input_path) as img:
                # 缩放
                if params.resize_mode != "none" and params.resize_value > 0:
                    img = resize_image(
                        img, params.resize_mode,
                        params.resize_value, params.keep_aspect_ratio,
                    )

                # 转换色彩模式
                if img.mode in ("RGBA", "LA", "PA"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")

                # 保存
                output_path.parent.mkdir(parents=True, exist_ok=True)
                save_kwargs = {"format": "WEBP", "method": 4}

                if params.lossless:
                    save_kwargs["lossless"] = True
                else:
                    save_kwargs["quality"] = params.quality

                img.save(str(output_path), **save_kwargs)

            elapsed = time.time() - start_time
            compressed_size = output_path.stat().st_size if output_path.exists() else 0

            return CompressResult(
                success=True,
                input_path=str(input_path),
                output_path=str(output_path),
                original_size=original_size,
                compressed_size=compressed_size,
                elapsed_seconds=elapsed,
            )

        except Exception as e:
            return CompressResult(
                success=False,
                input_path=str(input_path),
                output_path=str(output_path),
                original_size=original_size,
                elapsed_seconds=time.time() - start_time,
                error=str(e),
            )

    def get_info(self, path: Path) -> Optional[ImageInfo]:
        try:
            with Image.open(path) as img:
                return ImageInfo(
                    width=img.width,
                    height=img.height,
                    format=img.format or "WEBP",
                    file_size=path.stat().st_size,
                    has_alpha=img.mode in ("RGBA", "LA", "PA"),
                )
        except Exception:
            return None


register_handler(WebPHandler())
