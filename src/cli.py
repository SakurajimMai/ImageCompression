"""
Image Compression CLI — 命令行入口

使用方法:
    python cli.py compress INPUT_DIR -f avif -q 55 -o OUTPUT_DIR
    python cli.py compress INPUT_DIR --preset web
    python cli.py compress INPUT_DIR -f webp --lossless --recursive
    python cli.py info IMAGE_PATH
    python cli.py presets
    echo "path/to/dir" | python cli.py compress --stdin -f avif
"""
import sys
import time
from pathlib import Path

import click

# 确保 src/ 在 path 中
sys.path.insert(0, str(Path(__file__).parent))

from engine.formats.base import CompressParams
from engine.formats.registry import get_handler, list_handlers
from engine.pipeline import compress_batch
from engine.scanner import scan_directory
from engine.presets import get_preset, list_presets, PRESETS
from engine.stats import BatchStats


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _print_stats(stats: BatchStats):
    """打印压缩统计"""
    click.echo()
    click.secho("── 压缩统计 ──", fg="cyan", bold=True)
    click.echo(f"  文件总数:   {stats.total_files}")
    click.echo(f"  成功:       {stats.compressed_files}")
    if stats.failed_files > 0:
        click.secho(f"  失败:       {stats.failed_files}", fg="red")
    if stats.skipped_files > 0:
        click.echo(f"  跳过:       {stats.skipped_files}")
    click.echo(f"  原始大小:   {_format_size(stats.original_size)}")
    click.echo(f"  压缩后:     {_format_size(stats.compressed_size)}")
    click.secho(f"  节省:       {stats.saved_percent:.1f}%", fg="green", bold=True)
    click.echo(f"  耗时:       {stats.total_elapsed:.1f}s")
    if stats.speed_files_per_sec > 0:
        click.echo(f"  速度:       {stats.speed_files_per_sec:.1f} 张/秒")

    # 每张图详情
    if stats.results:
        click.echo()
        click.secho("── 文件详情 ──", fg="cyan")
        for r in stats.results:
            name = Path(r.input_path).name
            if r.success:
                ratio = f"{r.saved_percent:.0f}%"
                click.echo(
                    f"  ✓ {name:30s}  "
                    f"{_format_size(r.original_size):>8s} → {_format_size(r.compressed_size):>8s}  "
                    f"节省 {ratio:>5s}  {r.elapsed_seconds:.1f}s"
                )
            else:
                click.secho(f"  ✗ {name:30s}  {r.error}", fg="red")

    if stats.errors:
        click.echo()
        click.secho(f"── {len(stats.errors)} 个错误 ──", fg="red")
        for err in stats.errors[:20]:
            click.echo(f"  {err}")


@click.group()
@click.version_option(version="1.0.0", prog_name="Image Compression")
def cli():
    """Image Compression — 高性能图片压缩工具"""
    pass


@cli.command()
@click.argument("input_dir", required=False, type=click.Path(exists=True))
@click.option("-f", "--format", "fmt", default="avif",
              type=click.Choice(["avif", "webp", "jpeg"], case_sensitive=False),
              help="输出格式")
@click.option("-o", "--output", "output_dir", type=click.Path(),
              help="输出目录（默认: <输入目录>_<格式>）")
@click.option("-q", "--quality", type=click.IntRange(0, 100), default=None,
              help="压缩质量 (0-100)")
@click.option("-s", "--speed", type=click.IntRange(0, 10), default=6,
              help="AVIF 编码速度 (0=最慢最好, 10=最快)")
@click.option("--preset", type=click.Choice(list(PRESETS.keys())),
              help="使用预设模板")
@click.option("--lossless", is_flag=True, help="无损压缩")
@click.option("--recursive", "-r", is_flag=True, help="递归处理子目录")
@click.option("--overwrite", is_flag=True, help="覆盖原文件")
@click.option("--yuv", type=click.Choice(["420", "422", "444"]), default="420",
              help="YUV 采样格式")
@click.option("--depth", type=click.Choice(["8", "10", "12"]), default="8",
              help="位深度")
@click.option("--progressive", is_flag=True, help="渐进式输出")
@click.option("--workers", "-j", type=int, default=1,
              help="并行线程数")
@click.option("--conflict", type=click.Choice(["overwrite", "skip", "rename"]),
              default="overwrite", help="同名文件策略")
@click.option("--retries", type=int, default=1, help="失败重试次数")
@click.option("--strip-exif/--keep-exif", default=True, help="清除/保留 EXIF")
@click.option("--keep-icc/--strip-icc", default=True, help="保留/清除 ICC Profile")
@click.option("--strip-xmp/--keep-xmp", default=True, help="清除/保留 XMP")
@click.option("--resize", type=str, default=None,
              help="缩放 (如 'w800' 按宽度, 'h600' 按高度, '50%%' 按比例)")
@click.option("--stdin", "use_stdin", is_flag=True,
              help="从 stdin 读取输入目录路径")
@click.option("--quiet", is_flag=True, help="安静模式")
def compress(input_dir, fmt, output_dir, quality, speed, preset, lossless,
             recursive, overwrite, yuv, depth, progressive, workers,
             conflict, retries, strip_exif, keep_icc, strip_xmp,
             resize, use_stdin, quiet):
    """压缩图片目录"""
    # stdin 模式
    if use_stdin:
        input_dir = sys.stdin.readline().strip()
        if not input_dir:
            click.secho("错误: stdin 未提供输入路径", fg="red", err=True)
            sys.exit(1)

    if not input_dir:
        click.secho("错误: 请指定输入目录", fg="red", err=True)
        sys.exit(1)

    input_path = Path(input_dir)
    if not input_path.exists():
        click.secho(f"错误: 目录不存在 '{input_dir}'", fg="red", err=True)
        sys.exit(1)

    # 构建参数
    if preset:
        params = get_preset(preset)
        if not quiet:
            click.secho(f"使用预设: {PRESETS[preset]['display_name']}", fg="cyan")
    else:
        params = CompressParams(
            quality=quality if quality is not None else 55,
            speed=speed,
            lossless=lossless,
            strip_exif=strip_exif,
            keep_icc=keep_icc,
            strip_xmp=strip_xmp,
            extra={"yuv": yuv, "depth": int(depth), "progressive": progressive},
        )

    # 覆盖预设参数
    if quality is not None and preset:
        params.quality = quality
    if lossless:
        params.lossless = True

    # 缩放参数
    if resize:
        if resize.startswith("w"):
            params.resize_mode = "width"
            params.resize_value = int(resize[1:])
        elif resize.startswith("h"):
            params.resize_mode = "height"
            params.resize_value = int(resize[1:])
        elif resize.endswith("%"):
            params.resize_mode = "percent"
            params.resize_value = int(resize[:-1])

    # 输出目录
    if not output_dir and not overwrite:
        output_dir = str(input_path.parent / f"{input_path.name}_{fmt}")

    if not quiet:
        click.secho(f"输入: {input_dir}", fg="blue")
        click.secho(f"输出: {'覆盖原文件' if overwrite else output_dir}", fg="blue")
        click.secho(f"格式: {fmt.upper()}", fg="blue")
        if recursive:
            click.echo(f"模式: 递归")
        click.echo()

    # 进度回调
    def progress(current, total, msg, spd):
        if not quiet:
            bar = "█" * int(current / total * 30) + "░" * (30 - int(current / total * 30))
            click.echo(
                f"\r  [{bar}] {current}/{total} {spd:.1f}张/秒 {msg[:40]:40s}",
                nl=False,
            )

    # 执行压缩
    stats = compress_batch(
        input_dir=input_dir,
        output_dir=output_dir or input_dir,
        format_name=fmt,
        params=params,
        overwrite=overwrite,
        recursive=recursive,
        max_workers=workers,
        conflict_strategy=conflict,
        max_retries=retries,
        progress_callback=progress,
    )

    if not quiet:
        click.echo()  # 换行
        _print_stats(stats)


@cli.command()
@click.argument("image_path", type=click.Path(exists=True))
def info(image_path):
    """查看图片信息"""
    from engine.metadata import get_metadata_info

    path = Path(image_path)
    click.secho(f"文件: {path.name}", fg="cyan", bold=True)
    click.echo(f"大小: {_format_size(path.stat().st_size)}")

    # 格式信息
    for handler in list_handlers():
        img_info = handler.get_info(path)
        if img_info:
            click.echo(f"尺寸: {img_info.width} × {img_info.height}")
            click.echo(f"格式: {img_info.format}")
            click.echo(f"透明: {'是' if img_info.has_alpha else '否'}")
            break

    # 元数据信息
    meta = get_metadata_info(path)
    click.echo(f"EXIF: {'有 ({} 字段)'.format(meta['exif_fields']) if meta['has_exif'] else '无'}")
    click.echo(f"ICC:  {'有' if meta['has_icc'] else '无'}")
    click.echo(f"XMP:  {'有' if meta['has_xmp'] else '无'}")


@cli.command("scan")
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("-r", "--recursive", is_flag=True, help="递归子目录")
def scan_cmd(input_dir, recursive):
    """扫描目录统计"""
    result = scan_directory(input_dir, recursive=recursive)
    click.secho(f"目录: {input_dir}", fg="cyan", bold=True)
    click.echo(f"图片: {result.image_count} 张")
    click.echo(f"视频: {result.video_count} 个")
    click.echo(f"总大小: {result.total_size_mb:.1f} MB")
    if result.subdirs > 0:
        click.echo(f"子目录: {result.subdirs} 个")


@cli.command("presets")
def presets_cmd():
    """列出可用预设"""
    click.secho("── 可用预设 ──", fg="cyan", bold=True)
    for p in list_presets():
        click.echo(f"  {p['name']:15s} {p['display_name']:10s}  {p['description']}")


if __name__ == "__main__":
    cli()
