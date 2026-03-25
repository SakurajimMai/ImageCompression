"""
元数据处理模块 — EXIF / ICC / XMP 细粒度控制
"""
from pathlib import Path
from typing import Optional

from PIL import Image, ExifTags


def process_metadata(
    image_path: Path,
    output_path: Optional[Path] = None,
    strip_exif: bool = True,
    keep_icc: bool = True,
    strip_xmp: bool = True,
) -> Path:
    """
    处理图片元数据

    Args:
        image_path: 输入图片路径
        output_path: 输出路径（None=原地修改）
        strip_exif: 清除 EXIF 数据
        keep_icc: 保留 ICC Profile（色彩管理需要）
        strip_xmp: 清除 XMP 数据
    """
    if output_path is None:
        output_path = image_path

    with Image.open(image_path) as img:
        # 处理 EXIF 方向信息 — 先应用旋转再去除 EXIF
        if strip_exif:
            img = _apply_exif_orientation(img)

        # 收集要保留的信息
        icc_profile = None
        if keep_icc:
            icc_profile = img.info.get("icc_profile")

        # 创建干净的图片（去除所有元数据）
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))

        # 保存时附加需要保留的信息
        save_kwargs = {}
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile

        # 检测格式
        fmt = img.format or _guess_format(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        clean.save(str(output_path), format=fmt, **save_kwargs)

    return output_path


def get_metadata_info(image_path: Path) -> dict:
    """获取图片元数据信息"""
    info = {
        "has_exif": False,
        "has_icc": False,
        "has_xmp": False,
        "exif_fields": 0,
        "orientation": None,
    }

    try:
        with Image.open(image_path) as img:
            # EXIF
            exif_data = img.getexif()
            if exif_data:
                info["has_exif"] = True
                info["exif_fields"] = len(exif_data)
                # 方向
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, "")
                    if tag_name == "Orientation":
                        info["orientation"] = value

            # ICC
            if img.info.get("icc_profile"):
                info["has_icc"] = True

            # XMP
            if img.info.get("xmp") or img.info.get("XML:com.adobe.xmp"):
                info["has_xmp"] = True

    except Exception:
        pass

    return info


def _apply_exif_orientation(img: Image.Image) -> Image.Image:
    """根据 EXIF 方向标签旋转/翻转图片"""
    try:
        exif = img.getexif()
        orientation_tag = None
        for tag_id, value in exif.items():
            if ExifTags.TAGS.get(tag_id) == "Orientation":
                orientation_tag = value
                break

        if orientation_tag is None:
            return img

        transforms = {
            2: Image.Transpose.FLIP_LEFT_RIGHT,
            3: Image.Transpose.ROTATE_180,
            4: Image.Transpose.FLIP_TOP_BOTTOM,
            5: Image.Transpose.TRANSPOSE,
            6: Image.Transpose.ROTATE_270,
            7: Image.Transpose.TRANSVERSE,
            8: Image.Transpose.ROTATE_90,
        }
        if orientation_tag in transforms:
            return img.transpose(transforms[orientation_tag])

    except Exception:
        pass

    return img


def _guess_format(path: Path) -> str:
    """根据扩展名猜测图片格式"""
    ext_map = {
        ".jpg": "JPEG", ".jpeg": "JPEG",
        ".png": "PNG",
        ".webp": "WEBP",
        ".bmp": "BMP",
        ".gif": "GIF",
        ".tiff": "TIFF", ".tif": "TIFF",
    }
    return ext_map.get(path.suffix.lower(), "PNG")
