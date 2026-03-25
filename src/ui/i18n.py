"""
国际化 (i18n) 模块 — 中文 / 英文 双语支持
"""
from typing import Optional

_current_lang = "zh"

# 翻译字典
_translations = {
    # ── 通用 ──
    "app.title": {"zh": "Image Compression", "en": "Image Compression"},
    "common.ready": {"zh": "就绪", "en": "Ready"},
    "common.browse": {"zh": "浏览", "en": "Browse"},
    "common.start": {"zh": "开始", "en": "Start"},
    "common.close": {"zh": "关闭", "en": "Close"},
    "common.cancel": {"zh": "取消", "en": "Cancel"},
    "common.confirm": {"zh": "确认", "en": "Confirm"},
    "common.tip": {"zh": "提示", "en": "Notice"},
    "common.error": {"zh": "错误", "en": "Error"},
    "common.success": {"zh": "成功", "en": "Success"},
    "common.warning": {"zh": "警告", "en": "Warning"},
    "common.yes": {"zh": "是", "en": "Yes"},
    "common.no": {"zh": "否", "en": "No"},

    # ── Tab 标签 ──
    "tab.prepare": {"zh": " 准备 ", "en": " Prepare "},
    "tab.compress": {"zh": " 压缩 ", "en": " Compress "},
    "tab.upload": {"zh": " 上传 ", "en": " Upload "},
    "tab.settings": {"zh": " 设置 ", "en": " Settings "},
    "tab.help": {"zh": " 说明 ", "en": " Help "},

    # ── 按钮 ──
    "btn.run_all": {"zh": "  一键执行  ", "en": "  Run All  "},
    "btn.run_all_tip": {"zh": "依次执行：准备 → 压缩 → 上传", "en": "Execute: Prepare → Compress → Upload"},
    "btn.compress": {"zh": "开始压缩", "en": "Compress"},
    "btn.preview": {"zh": "预览对比", "en": "Preview"},
    "btn.scan": {"zh": "扫描", "en": "Scan"},
    "btn.upload": {"zh": "开始上传", "en": "Upload"},
    "btn.prepare": {"zh": "开始处理", "en": "Process"},

    # ── 准备页 ──
    "prepare.input_dir": {"zh": "输入目录", "en": "Input Directory"},
    "prepare.output_dir": {"zh": "输出目录", "en": "Output Directory"},
    "prepare.input_placeholder": {"zh": "选择图片目录...", "en": "Select image directory..."},
    "prepare.options": {"zh": "处理选项", "en": "Options"},
    "prepare.rename_images": {"zh": "重命名图片 (0001.jpg...)", "en": "Rename images (0001.jpg...)"},
    "prepare.rename_videos": {"zh": "重命名视频 (video001.mp4...)", "en": "Rename videos (video001.mp4...)"},
    "prepare.strip_exif": {"zh": "清除 EXIF 元数据", "en": "Strip EXIF metadata"},
    "prepare.recursive": {"zh": "递归扫描子目录", "en": "Scan subdirectories"},
    "prepare.recursive_tip": {"zh": "递归处理子文件夹中的图片", "en": "Process images in subfolders"},
    "prepare.scan_result": {"zh": "扫描结果", "en": "Scan Result"},
    "prepare.mode_new": {"zh": "输出到新目录", "en": "Output to new directory"},
    "prepare.mode_overwrite": {"zh": "覆盖原文件", "en": "Overwrite originals"},

    # ── 压缩页 ──
    "compress.input_dir": {"zh": "输入目录", "en": "Input Directory"},
    "compress.input_placeholder": {"zh": "选择图片目录（可从「准备」步骤自动填充）...", "en": "Select directory (auto-filled from Prepare)..."},
    "compress.settings": {"zh": "压缩设置", "en": "Compression Settings"},
    "compress.format": {"zh": "输出格式:", "en": "Output format:"},
    "compress.quality_min": {"zh": "质量下限:", "en": "Min quality:"},
    "compress.quality_max": {"zh": "质量上限:", "en": "Max quality:"},
    "compress.speed": {"zh": "速度:", "en": "Speed:"},
    "compress.threads": {"zh": "线程:", "en": "Threads:"},
    "compress.threads_all": {"zh": "全部", "en": "All"},
    "compress.yuv": {"zh": "YUV:", "en": "YUV:"},
    "compress.depth": {"zh": "位深:", "en": "Depth:"},
    "compress.alpha": {"zh": "Alpha 独立质量", "en": "Independent Alpha quality"},
    "compress.alpha_min": {"zh": "下限:", "en": "Min:"},
    "compress.alpha_max": {"zh": "上限:", "en": "Max:"},
    "compress.lossless": {"zh": "无损压缩", "en": "Lossless"},
    "compress.progressive": {"zh": "渐进式输出", "en": "Progressive"},
    "compress.progressive_tip": {"zh": "libavif 1.1+ 支持渐进式加载", "en": "Requires libavif 1.1+"},
    "compress.quality": {"zh": "质量:", "en": "Quality:"},
    "compress.resize": {"zh": "缩放:", "en": "Resize:"},
    "compress.resize_none": {"zh": "不缩放", "en": "None"},
    "compress.resize_width": {"zh": "按宽度", "en": "By width"},
    "compress.resize_height": {"zh": "按高度", "en": "By height"},
    "compress.resize_percent": {"zh": "按比例(%)", "en": "By percent(%)"},
    "compress.keep_ratio": {"zh": "保持纵横比", "en": "Keep aspect ratio"},
    "compress.output_settings": {"zh": "输出设置", "en": "Output Settings"},
    "compress.output_new": {"zh": "输出到新目录", "en": "Output to new directory"},
    "compress.output_overwrite": {"zh": "覆盖原文件", "en": "Overwrite originals"},
    "compress.output_placeholder": {"zh": "输出目录...", "en": "Output directory..."},
    "compress.recursive": {"zh": "递归子目录", "en": "Recursive"},
    "compress.recursive_tip": {"zh": "递归处理子文件夹，保持目录结构", "en": "Process subfolders, keep structure"},
    "compress.conflict": {"zh": "同名文件:", "en": "Conflict:"},
    "compress.conflict_overwrite": {"zh": "覆盖", "en": "Overwrite"},
    "compress.conflict_skip": {"zh": "跳过", "en": "Skip"},
    "compress.conflict_rename": {"zh": "重命名", "en": "Rename"},
    "compress.workers": {"zh": "并行数:", "en": "Workers:"},
    "compress.workers_tip": {"zh": "WebP/JPEG 可并行；AVIF 使用自带多线程", "en": "WebP/JPEG parallel; AVIF uses built-in threading"},
    "compress.hdr": {"zh": "HDR / Gain Map", "en": "HDR / Gain Map"},
    "compress.gainmap_quality": {"zh": "Gain Map 质量:", "en": "Gain Map quality:"},
    "compress.gainmap_tip": {"zh": "libavif 1.4+ 支持 Apple 式 Gain Map", "en": "libavif 1.4+ Apple-style Gain Map"},

    # ── 状态信息 ──
    "status.compressing": {"zh": "压缩:", "en": "Compressing:"},
    "status.done": {"zh": "完成", "en": "Done"},
    "status.compressed": {"zh": "已压缩", "en": "compressed"},
    "status.skipped": {"zh": "跳过", "en": "skipped"},
    "status.failed": {"zh": "失败", "en": "failed"},
    "status.original": {"zh": "原始:", "en": "Original:"},
    "status.after": {"zh": "压缩后:", "en": "After:"},
    "status.saved": {"zh": "节省", "en": "Saved"},
    "status.speed": {"zh": "速度:", "en": "Speed:"},
    "status.fps": {"zh": "张/秒", "en": "files/s"},
    "status.phase_1": {"zh": "阶段 1/3 · 准备中...", "en": "Phase 1/3 · Preparing..."},
    "status.phase_2": {"zh": "阶段 2/3 · 压缩中...", "en": "Phase 2/3 · Compressing..."},
    "status.phase_3": {"zh": "阶段 3/3 · 上传中...", "en": "Phase 3/3 · Uploading..."},
    "status.all_done": {"zh": "全部完成!", "en": "All done!"},
    "status.interrupted": {"zh": "执行中断", "en": "Interrupted"},

    # ── 扫描 ──
    "scan.images": {"zh": "张图片", "en": "images"},
    "scan.videos": {"zh": "个视频", "en": "videos"},
    "scan.total": {"zh": "共", "en": "Total"},
    "scan.subdirs": {"zh": "个子目录", "en": "subdirectories"},

    # ── 预览 ──
    "preview.title": {"zh": "压缩预览对比", "en": "Compression Preview"},
    "preview.select_file": {"zh": "选择文件:", "en": "Select file:"},
    "preview.prev": {"zh": "◀ 上一张", "en": "◀ Previous"},
    "preview.next": {"zh": "下一张 ▶", "en": "Next ▶"},
    "preview.original": {"zh": "原始图片", "en": "Original"},
    "preview.compressed": {"zh": "压缩后", "en": "Compressed"},

    # ── 设置 ──
    "settings.language": {"zh": "界面语言:", "en": "Language:"},
    "settings.theme": {"zh": "界面主题:", "en": "Theme:"},
    "settings.theme_light": {"zh": "浅色", "en": "Light"},
    "settings.theme_dark": {"zh": "深色", "en": "Dark"},
    "settings.default_format": {"zh": "默认输出格式:", "en": "Default format:"},
    "settings.default_quality": {"zh": "默认质量:", "en": "Default quality:"},
    "settings.restart_required": {"zh": "语言/主题更改将在重启后生效", "en": "Language/theme changes take effect after restart"},

    # ── 错误 ──
    "error.no_input": {"zh": "请先选择输入目录", "en": "Please select input directory"},
    "error.no_avifenc": {
        "zh": "AVIF 压缩需要 avifenc，请先安装 libavif。\n\nWindows: scoop install libavif\nmacOS: brew install libavif\nLinux: apt install libavif-bin",
        "en": "AVIF compression requires avifenc.\n\nWindows: scoop install libavif\nmacOS: brew install libavif\nLinux: apt install libavif-bin",
    },
    "error.avifenc_not_found": {"zh": "未找到 avifenc", "en": "avifenc not found"},
    "error.partial_fail": {"zh": "部分文件失败", "en": "Some files failed"},
    "error.compress_fail": {"zh": "压缩失败", "en": "Compression failed"},
    "error.scan_fail": {"zh": "扫描失败", "en": "Scan failed"},
}


def set_language(lang: str):
    """设置当前语言 (zh / en)"""
    global _current_lang
    if lang in ("zh", "en"):
        _current_lang = lang


def get_language() -> str:
    """获取当前语言"""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """翻译文本"""
    entry = _translations.get(key)
    if entry is None:
        return key

    text = entry.get(_current_lang, entry.get("zh", key))

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return text
