"""
AVIF 格式处理器 — 通过 avifenc CLI 实现

支持 libavif 1.4 新特性：
- YUV 格式 (420/422/444)
- 位深度 (8/10/12)
- Alpha 独立质量
- 无损模式
- 渐进式输出
- HDR / Gain Map
"""
import subprocess
import time
from pathlib import Path
from typing import Optional

from PIL import Image

from engine.formats.base import (
    FormatHandler, CompressResult, CompressParams, ImageInfo,
)
from engine.formats.registry import register_handler
from engine.resizer import resize_image


class AVIFHandler(FormatHandler):
    """AVIF 格式处理器（avifenc wrapper）"""

    def __init__(self, avifenc_path: str = "avifenc"):
        self._avifenc_path = avifenc_path

    @property
    def name(self) -> str:
        return "avif"

    @property
    def display_name(self) -> str:
        return "AVIF"

    @property
    def extensions(self) -> list[str]:
        return [".avif"]

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

        # 缩放预处理（如果需要）
        temp_input = input_path
        need_cleanup = False

        if params.resize_mode != "none" and params.resize_value > 0:
            try:
                with Image.open(input_path) as img:
                    resized = resize_image(
                        img, params.resize_mode,
                        params.resize_value, params.keep_aspect_ratio,
                    )
                    # 保存为临时 PNG 供 avifenc 处理
                    temp_input = output_path.parent / f"_temp_{input_path.stem}.png"
                    temp_input.parent.mkdir(parents=True, exist_ok=True)
                    resized.save(str(temp_input), format="PNG")
                    need_cleanup = True
            except Exception as e:
                return CompressResult(
                    success=False,
                    input_path=str(input_path),
                    output_path=str(output_path),
                    original_size=original_size,
                    error=f"缩放失败: {e}",
                )

        # 构建 avifenc 命令
        cmd = self._build_command(temp_input, output_path, params)

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )

            elapsed = time.time() - start_time

            if result.returncode != 0:
                return CompressResult(
                    success=False,
                    input_path=str(input_path),
                    output_path=str(output_path),
                    original_size=original_size,
                    elapsed_seconds=elapsed,
                    error=result.stderr.strip() or f"avifenc 返回码 {result.returncode}",
                )

            compressed_size = output_path.stat().st_size if output_path.exists() else 0

            return CompressResult(
                success=True,
                input_path=str(input_path),
                output_path=str(output_path),
                original_size=original_size,
                compressed_size=compressed_size,
                elapsed_seconds=elapsed,
            )

        except subprocess.TimeoutExpired:
            return CompressResult(
                success=False,
                input_path=str(input_path),
                output_path=str(output_path),
                original_size=original_size,
                elapsed_seconds=time.time() - start_time,
                error="avifenc 处理超时 (10分钟)",
            )
        except FileNotFoundError:
            return CompressResult(
                success=False,
                input_path=str(input_path),
                output_path=str(output_path),
                original_size=original_size,
                error=f"avifenc 未找到: {self._avifenc_path}",
            )
        finally:
            if need_cleanup and temp_input.exists():
                temp_input.unlink(missing_ok=True)

    def _build_command(
        self, input_path: Path, output_path: Path, params: CompressParams,
    ) -> list[str]:
        """构建 avifenc 命令行"""
        extra = params.extra
        cmd = [self._avifenc_path]

        # 无损模式
        if params.lossless:
            cmd.append("--lossless")
        else:
            # 质量参数
            quality = params.quality
            min_q = extra.get("min_quality", max(0, quality - 10))
            max_q = extra.get("max_quality", min(63, quality))
            cmd.extend(["--min", str(min_q), "--max", str(max_q)])

        # 速度
        cmd.extend(["--speed", str(params.speed)])

        # 线程
        threads = extra.get("threads", "all")
        cmd.extend(["-j", str(threads)])

        # YUV 格式
        yuv = extra.get("yuv", "420")
        cmd.extend(["--yuv", str(yuv)])

        # 位深度
        depth = extra.get("depth", 8)
        cmd.extend(["--depth", str(depth)])

        # Alpha 独立质量
        alpha_min = extra.get("alpha_min")
        alpha_max = extra.get("alpha_max")
        if alpha_min is not None and alpha_max is not None:
            cmd.extend(["--alpha-min", str(alpha_min)])
            cmd.extend(["--alpha-max", str(alpha_max)])

        # 渐进式
        if extra.get("progressive", False):
            cmd.append("--progressive")

        # HDR / Gain Map (libavif 1.4+)
        gain_map_quality = extra.get("gain_map_quality")
        if gain_map_quality is not None:
            cmd.extend(["--gain-map-quality", str(gain_map_quality)])

        # 元数据控制
        if params.strip_exif and not params.keep_icc:
            cmd.append("--ignore-exif")
            cmd.append("--ignore-icc")
        elif params.strip_exif:
            cmd.append("--ignore-exif")

        if params.strip_xmp:
            cmd.append("--ignore-xmp")

        cmd.extend([str(input_path), str(output_path)])
        return cmd

    def get_info(self, path: Path) -> Optional[ImageInfo]:
        """获取图片信息"""
        try:
            with Image.open(path) as img:
                return ImageInfo(
                    width=img.width,
                    height=img.height,
                    format=img.format or path.suffix.lstrip(".").upper(),
                    file_size=path.stat().st_size,
                    has_alpha=img.mode in ("RGBA", "LA", "PA"),
                    bit_depth=8,
                )
        except Exception:
            return None

    def check_available(self) -> tuple[bool, str]:
        """检查 avifenc 是否可用"""
        try:
            result = subprocess.run(
                [self._avifenc_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = result.stdout.strip() or result.stderr.strip()
            return True, version
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False, "avifenc 未找到"


# 自注册
register_handler(AVIFHandler())
