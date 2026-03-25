"""
图片缩放模块 — 支持 7 种缩放模式

模式:
  none      - 不缩放
  width     - 按目标宽度（保持比例）
  height    - 按目标高度（保持比例）
  percent   - 按百分比
  long_edge - 限制长边（短边按比例）
  short_edge- 限制短边（长边按比例）
  fit       - 缩小到指定框内（保持比例，不裁剪）
  fill      - 缩放+居中裁剪到指定尺寸
  exact     - 强制拉伸到指定尺寸（不保持比例）
"""
from PIL import Image


def resize_image(
    img: Image.Image,
    mode: str,
    value: int = 0,
    keep_aspect_ratio: bool = True,
    target_width: int = 0,
    target_height: int = 0,
) -> Image.Image:
    """
    缩放图片

    Args:
        img: PIL Image 对象
        mode: 缩放模式
        value: 目标值（宽度/高度/百分比/长短边像素）
        keep_aspect_ratio: 是否保持纵横比（旧接口兼容）
        target_width: fit/fill/exact 模式的目标宽度
        target_height: fit/fill/exact 模式的目标高度
    """
    if mode == "none" or (value <= 0 and target_width <= 0 and target_height <= 0):
        return img

    w, h = img.size

    if mode == "width":
        new_w = value
        new_h = int(h * (value / w)) if keep_aspect_ratio else h

    elif mode == "height":
        new_h = value
        new_w = int(w * (value / h)) if keep_aspect_ratio else w

    elif mode == "percent":
        new_w = max(1, int(w * value / 100))
        new_h = max(1, int(h * value / 100))

    elif mode == "long_edge":
        # 限制长边，短边按比例
        long = max(w, h)
        if long <= value:
            return img  # 不放大
        scale = value / long
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

    elif mode == "short_edge":
        # 限制短边，长边按比例
        short = min(w, h)
        if short <= value:
            return img  # 不放大
        scale = value / short
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

    elif mode == "fit":
        # 缩小到框内（保持比例，不裁剪）
        tw, th = target_width or value, target_height or value
        scale = min(tw / w, th / h)
        if scale >= 1:
            return img  # 不放大
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

    elif mode == "fill":
        # 缩放 + 居中裁剪
        tw, th = target_width or value, target_height or value
        scale = max(tw / w, th / h)
        temp_w = max(1, int(w * scale))
        temp_h = max(1, int(h * scale))
        img = img.resize((temp_w, temp_h), Image.Resampling.LANCZOS)
        # 居中裁剪
        left = (temp_w - tw) // 2
        top = (temp_h - th) // 2
        return img.crop((left, top, left + tw, top + th))

    elif mode == "exact":
        # 强制拉伸
        tw, th = target_width or value, target_height or value
        return img.resize((tw, th), Image.Resampling.LANCZOS)

    else:
        return img

    new_w = max(1, new_w)
    new_h = max(1, new_h)
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
