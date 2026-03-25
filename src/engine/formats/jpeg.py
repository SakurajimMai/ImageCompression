"""
JPEG 格式处理器 — 通过 Pillow 实现
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


class JPEGHandler(FormatHandler):
    """JPEG 格式处理器"""

    @property
    def name(self) -> str:
        return "jpeg"

    @property
    def display_name(self) -> str:
        return "JPEG"

    @property
    def extensions(self) -> list[str]:
        return [".jpg", ".jpeg"]

    @property
    def supports_lossless(self) -> bool:
        return False  # JPEG 不支持无损

    @property
    def supports_alpha(self) -> bool:
        return False  # JPEG 不支持透明

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

                # JPEG 不支持透明，强制转 RGB
                if img.mode in ("RGBA", "LA", "PA", "P"):
                    img = img.convert("RGB")
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                output_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(
                    str(output_path),
                    format="JPEG",
                    quality=params.quality,
                    subsampling=0,  # 4:4:4 最高质量
                    optimize=True,
                )

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
                    format=img.format or "JPEG",
                    file_size=path.stat().st_size,
                    has_alpha=False,
                )
        except Exception:
            return None


register_handler(JPEGHandler())
