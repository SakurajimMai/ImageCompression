"""
格式处理器基类 — 所有输出格式必须实现此接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ImageInfo:
    """图片基本信息"""
    width: int
    height: int
    format: str
    file_size: int  # 字节
    has_alpha: bool = False
    bit_depth: int = 8
    color_space: str = "sRGB"


@dataclass
class CompressResult:
    """单文件压缩结果"""
    success: bool
    input_path: str
    output_path: str
    original_size: int = 0       # 字节
    compressed_size: int = 0     # 字节
    elapsed_seconds: float = 0.0
    error: str = ""

    @property
    def ratio(self) -> float:
        """压缩比（0-1，越小压缩越多）"""
        if self.original_size == 0:
            return 0
        return self.compressed_size / self.original_size

    @property
    def saved_percent(self) -> float:
        """节省百分比"""
        return (1 - self.ratio) * 100


@dataclass
class CompressParams:
    """通用压缩参数"""
    quality: int = 60
    speed: int = 6
    lossless: bool = False

    # 缩放
    resize_mode: str = "none"    # none / width / height / percent
    resize_value: int = 0
    keep_aspect_ratio: bool = True

    # 元数据
    strip_exif: bool = True
    keep_icc: bool = True
    strip_xmp: bool = True

    # 额外格式参数（各格式自行解析）
    extra: dict = field(default_factory=dict)


class FormatHandler(ABC):
    """格式处理器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """格式名称，如 'avif', 'webp', 'jpeg'"""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """显示名称，如 'AVIF', 'WebP'"""
        ...

    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        """输出文件扩展名列表，如 ['.avif']"""
        ...

    @property
    @abstractmethod
    def supports_lossless(self) -> bool:
        ...

    @property
    @abstractmethod
    def supports_alpha(self) -> bool:
        ...

    @abstractmethod
    def compress(
        self,
        input_path: Path,
        output_path: Path,
        params: CompressParams,
    ) -> CompressResult:
        """压缩单个文件"""
        ...

    @abstractmethod
    def get_info(self, path: Path) -> Optional[ImageInfo]:
        """获取图片信息"""
        ...

    def default_extension(self) -> str:
        """默认输出扩展名"""
        return self.extensions[0]
