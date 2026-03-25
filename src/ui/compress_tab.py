"""
压缩页 Tab — 使用 engine 管线，支持 AVIF 完整参数
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QCheckBox,
    QFileDialog, QGroupBox, QComboBox, QSpinBox, QMessageBox,
    QStackedWidget,
)
from PySide6.QtCore import QThread, Signal, Qt

from engine.formats.base import CompressParams
from engine.formats.registry import get_handler
from engine.pipeline import compress_batch
from engine.stats import BatchStats
from ui.widgets.card_group import create_card_group


class CompressWorker(QThread):
    progress = Signal(int, int, str, float)  # current, total, msg, speed
    finished = Signal(object)  # BatchStats
    error = Signal(str)

    def __init__(self, input_dir, output_dir, fmt, params, overwrite,
                 recursive, max_workers, conflict_strategy, max_retries):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.fmt = fmt
        self.params = params
        self.overwrite = overwrite
        self.recursive = recursive
        self.max_workers = max_workers
        self.conflict_strategy = conflict_strategy
        self.max_retries = max_retries

    def run(self):
        try:
            stats = compress_batch(
                input_dir=self.input_dir,
                output_dir=self.output_dir,
                format_name=self.fmt,
                params=self.params,
                overwrite=self.overwrite,
                recursive=self.recursive,
                max_workers=self.max_workers,
                conflict_strategy=self.conflict_strategy,
                max_retries=self.max_retries,
                progress_callback=lambda c, t, m, s: self.progress.emit(c, t, m, s),
            )
            self.finished.emit(stats)
        except Exception as e:
            import traceback
            self.error.emit(f"{e}\n\n{traceback.format_exc()}")


class CompressTab(QWidget):
    def __init__(self, config, progress_widget, parent=None):
        super().__init__(parent)
        self.config = config
        self.progress_widget = progress_widget
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(2, 2, 2, 2)

        # ── 输入目录 ──
        ig = QHBoxLayout()
        ig.setSpacing(4)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("选择图片目录（可从「准备」步骤自动填充）...")
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(70)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_input)
        ig.addWidget(self.input_edit, 1)
        ig.addWidget(browse_btn)
        layout.addLayout(create_card_group("输入目录", ig))

        # ── 压缩设置 ──
        format_group = QGroupBox("压缩设置")
        fg = QVBoxLayout(format_group)
        fg.setSpacing(4)

        # 输出格式
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["AVIF", "WebP", "JPEG"])
        self.format_combo.setFixedWidth(120)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        fmt_row.addWidget(self.format_combo)
        fmt_row.addStretch()
        fg.addLayout(fmt_row)

        # 参数切换
        self.params_stack = QStackedWidget()

        # --- AVIF 参数 ---
        avif_w = QWidget()
        avif_l = QVBoxLayout(avif_w)
        avif_l.setContentsMargins(0, 0, 0, 0)
        avif_l.setSpacing(3)

        # 质量 + 速度
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        row1.addWidget(QLabel("质量下限:"))
        self.avif_min = QSpinBox()
        self.avif_min.setRange(0, 63)
        self.avif_min.setValue(20)
        self.avif_min.setToolTip("越低文件越小，画质越差 (0-63)")
        row1.addWidget(self.avif_min)
        row1.addWidget(QLabel("质量上限:"))
        self.avif_max = QSpinBox()
        self.avif_max.setRange(0, 63)
        self.avif_max.setValue(40)
        row1.addWidget(self.avif_max)
        row1.addStretch()
        avif_l.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addWidget(QLabel("速度:"))
        self.avif_speed = QSpinBox()
        self.avif_speed.setRange(0, 10)
        self.avif_speed.setValue(6)
        self.avif_speed.setToolTip("0=最慢最好 10=最快最差")
        row2.addWidget(self.avif_speed)
        row2.addWidget(QLabel("线程:"))
        self.avif_threads = QComboBox()
        self.avif_threads.addItem("全部", "all")
        cpu_count = os.cpu_count() or 4
        for i in range(1, cpu_count + 1):
            self.avif_threads.addItem(str(i), str(i))
        row2.addWidget(self.avif_threads)
        row2.addStretch()
        avif_l.addLayout(row2)

        # YUV + 位深度
        row3 = QHBoxLayout()
        row3.setSpacing(6)
        row3.addWidget(QLabel("YUV:"))
        self.avif_yuv = QComboBox()
        self.avif_yuv.addItems(["420", "422", "444"])
        self.avif_yuv.setToolTip("420=最小 444=最高质量")
        row3.addWidget(self.avif_yuv)
        row3.addWidget(QLabel("位深:"))
        self.avif_depth = QComboBox()
        self.avif_depth.addItems(["8", "10", "12"])
        self.avif_depth.setToolTip("8=标准 10=HDR 12=专业")
        row3.addWidget(self.avif_depth)
        row3.addStretch()
        avif_l.addLayout(row3)

        # Alpha 质量
        row4 = QHBoxLayout()
        row4.setSpacing(6)
        self.chk_alpha = QCheckBox("Alpha 独立质量")
        self.chk_alpha.toggled.connect(self._on_alpha_toggled)
        row4.addWidget(self.chk_alpha)
        row4.addWidget(QLabel("下限:"))
        self.alpha_min = QSpinBox()
        self.alpha_min.setRange(0, 63)
        self.alpha_min.setValue(20)
        self.alpha_min.setEnabled(False)
        row4.addWidget(self.alpha_min)
        row4.addWidget(QLabel("上限:"))
        self.alpha_max = QSpinBox()
        self.alpha_max.setRange(0, 63)
        self.alpha_max.setValue(40)
        self.alpha_max.setEnabled(False)
        row4.addWidget(self.alpha_max)
        row4.addStretch()
        avif_l.addLayout(row4)

        # 无损 + 渐进式 + HDR
        row5 = QHBoxLayout()
        row5.setSpacing(10)
        self.chk_lossless = QCheckBox("无损压缩")
        self.chk_progressive = QCheckBox("渐进式输出")
        self.chk_progressive.setToolTip("libavif 1.1+ 支持渐进式加载")
        row5.addWidget(self.chk_lossless)
        row5.addWidget(self.chk_progressive)
        row5.addStretch()
        avif_l.addLayout(row5)

        self.params_stack.addWidget(avif_w)

        # --- WebP / JPEG 参数 ---
        simple_w = QWidget()
        simple_l = QVBoxLayout(simple_w)
        simple_l.setContentsMargins(0, 0, 0, 0)
        sq_row = QHBoxLayout()
        sq_row.addWidget(QLabel("质量:"))
        self.webp_quality = QSpinBox()
        self.webp_quality.setRange(1, 100)
        self.webp_quality.setValue(80)
        sq_row.addWidget(self.webp_quality)
        sq_row.addStretch()
        simple_l.addLayout(sq_row)
        self.chk_webp_lossless = QCheckBox("无损压缩")
        simple_l.addWidget(self.chk_webp_lossless)
        self.params_stack.addWidget(simple_w)

        fg.addWidget(self.params_stack)

        # ── 缩放设置 ──
        resize_row = QHBoxLayout()
        resize_row.setSpacing(6)
        resize_row.addWidget(QLabel("缩放:"))
        self.resize_mode = QComboBox()
        self.resize_mode.addItems([
            "不缩放", "按宽度", "按高度", "按比例(%)",
            "长边限制", "短边限制", "适应框内(fit)", "填充裁剪(fill)", "强制拉伸(exact)",
        ])
        self.resize_mode.setFixedWidth(110)
        self.resize_mode.currentIndexChanged.connect(self._on_resize_changed)
        resize_row.addWidget(self.resize_mode)
        self.resize_value = QSpinBox()
        self.resize_value.setRange(1, 99999)
        self.resize_value.setValue(800)
        self.resize_value.setEnabled(False)
        self.resize_value.setSuffix(" px")
        resize_row.addWidget(self.resize_value)
        self.chk_keep_ratio = QCheckBox("保持纵横比")
        self.chk_keep_ratio.setChecked(True)
        self.chk_keep_ratio.setEnabled(False)
        resize_row.addWidget(self.chk_keep_ratio)
        resize_row.addStretch()
        fg.addLayout(resize_row)

        layout.addLayout(create_card_group("压缩设置", fg))

        # ── 输出设置 ──
        og = QVBoxLayout()
        og.setSpacing(4)

        mode_row = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.mode_new = QRadioButton("输出到新目录")
        self.mode_overwrite = QRadioButton("覆盖原文件")
        self.mode_group.addButton(self.mode_new, 0)
        self.mode_group.addButton(self.mode_overwrite, 1)
        self.mode_new.setChecked(True)
        self.mode_new.toggled.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_new)
        mode_row.addWidget(self.mode_overwrite)
        mode_row.addStretch()
        og.addLayout(mode_row)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(4)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("输出目录...")
        self.output_browse = QPushButton("浏览")
        self.output_browse.setFixedWidth(70)
        self.output_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.output_browse.clicked.connect(self._browse_output)
        dir_row.addWidget(self.output_edit, 1)
        dir_row.addWidget(self.output_browse)
        og.addLayout(dir_row)

        # 处理选项
        opts_row = QHBoxLayout()
        opts_row.setSpacing(8)
        self.chk_recursive = QCheckBox("递归子目录")
        self.chk_recursive.setToolTip("递归处理子文件夹，保持目录结构")
        opts_row.addWidget(self.chk_recursive)

        opts_row.addWidget(QLabel("同名文件:"))
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItems(["覆盖", "跳过", "重命名"])
        self.conflict_combo.setFixedWidth(80)
        opts_row.addWidget(self.conflict_combo)

        opts_row.addWidget(QLabel("并行数:"))
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, os.cpu_count() or 4)
        self.workers_spin.setValue(1)
        self.workers_spin.setToolTip("WebP/JPEG 可并行；AVIF 使用自带多线程")
        opts_row.addWidget(self.workers_spin)

        opts_row.addStretch()
        og.addLayout(opts_row)

        layout.addLayout(create_card_group("输出设置", og))

        # ── 操作按钮 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.preview_btn = QPushButton("预览对比")
        self.preview_btn.setFixedWidth(100)
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_btn.setEnabled(False)
        self.preview_btn.clicked.connect(self._show_preview)
        btn_row.addWidget(self.preview_btn)
        self.run_btn = QPushButton("开始压缩")
        self.run_btn.setObjectName("actionBtn")
        self.run_btn.setFixedWidth(120)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._run)
        btn_row.addWidget(self.run_btn)
        layout.addLayout(btn_row)

        # ── 性能仪表盘 ──
        from ui.widgets.perf_monitor import PerfMonitor
        self.perf_monitor = PerfMonitor()
        layout.addWidget(self.perf_monitor)

        layout.addStretch()
        self._last_stats = None

    # ── 事件处理 ──
    def _browse_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if path:
            self.input_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_edit.setText(path)

    def _on_format_changed(self, index):
        self.params_stack.setCurrentIndex(0 if index == 0 else 1)
        # JPEG 不支持无损
        if index == 2:
            self.chk_webp_lossless.setEnabled(False)
            self.chk_webp_lossless.setChecked(False)
        else:
            self.chk_webp_lossless.setEnabled(True)

    def _on_mode_changed(self, checked):
        is_new = self.mode_new.isChecked()
        self.output_edit.setEnabled(is_new)
        self.output_browse.setEnabled(is_new)

    def _on_alpha_toggled(self, checked):
        self.alpha_min.setEnabled(checked)
        self.alpha_max.setEnabled(checked)

    def _on_resize_changed(self, index):
        enabled = index > 0
        self.resize_value.setEnabled(enabled)
        self.chk_keep_ratio.setEnabled(enabled)
        if index == 3:  # 按比例
            self.resize_value.setSuffix(" %")
            self.resize_value.setRange(1, 500)
            self.resize_value.setValue(50)
        elif index >= 6:  # fit/fill/exact
            self.resize_value.setSuffix(" px")
            self.resize_value.setRange(1, 99999)
            self.resize_value.setValue(800)
            self.chk_keep_ratio.setEnabled(False)  # 这些模式有自己的逻辑
        elif enabled:
            self.resize_value.setSuffix(" px")
            self.resize_value.setRange(1, 99999)
            self.resize_value.setValue(800)

    def _get_params(self) -> CompressParams:
        fmt = self.format_combo.currentText().lower()

        # 缩放参数
        resize_modes = [
            "none", "width", "height", "percent",
            "long_edge", "short_edge", "fit", "fill", "exact",
        ]
        resize_mode = resize_modes[self.resize_mode.currentIndex()]
        resize_value = self.resize_value.value() if resize_mode != "none" else 0

        if fmt == "avif":
            extra = {
                "min_quality": self.avif_min.value(),
                "max_quality": self.avif_max.value(),
                "threads": self.avif_threads.currentData(),
                "yuv": self.avif_yuv.currentText(),
                "depth": int(self.avif_depth.currentText()),
                "progressive": self.chk_progressive.isChecked(),
            }
            if self.chk_alpha.isChecked():
                extra["alpha_min"] = self.alpha_min.value()
                extra["alpha_max"] = self.alpha_max.value()

            return CompressParams(
                quality=self.avif_max.value(),
                speed=self.avif_speed.value(),
                lossless=self.chk_lossless.isChecked(),
                resize_mode=resize_mode,
                resize_value=resize_value,
                keep_aspect_ratio=self.chk_keep_ratio.isChecked(),
                extra=extra,
            )
        else:
            return CompressParams(
                quality=self.webp_quality.value(),
                lossless=self.chk_webp_lossless.isChecked(),
                resize_mode=resize_mode,
                resize_value=resize_value,
                keep_aspect_ratio=self.chk_keep_ratio.isChecked(),
            )

    def _run(self):
        if self.worker and self.worker.isRunning():
            return  # 防双击

        input_dir = self.input_edit.text().strip()
        if not input_dir:
            QMessageBox.warning(self, "提示", "请先选择输入目录")
            return

        fmt = self.format_combo.currentText().lower()
        overwrite = self.mode_overwrite.isChecked()
        output_dir = input_dir if overwrite else self.output_edit.text().strip()

        if not overwrite and not output_dir:
            from pathlib import Path
            p = Path(input_dir)
            output_dir = str(p.parent / f"{p.name}_{fmt}")
            self.output_edit.setText(output_dir)

        if fmt == "avif":
            handler = get_handler("avif")
            # 通过临时设置检查可用性，不永久修改单例
            avifenc = self.config.avifenc_path or "avifenc"
            old_path = handler._avifenc_path
            handler._avifenc_path = avifenc
            available, version = handler.check_available()
            if not available:
                handler._avifenc_path = old_path
                QMessageBox.critical(self, "未找到 avifenc",
                    "AVIF 压缩需要 avifenc，请先安装 libavif。\n\n"
                    "Windows: scoop install libavif\n"
                    "macOS: brew install libavif\n"
                    "Linux: apt install libavif-bin")
                return

        conflict_map = {"覆盖": "overwrite", "跳过": "skip", "重命名": "rename"}
        conflict = conflict_map.get(self.conflict_combo.currentText(), "overwrite")

        self.run_btn.setEnabled(False)
        self.progress_widget.reset()

        # 启动性能监控
        from engine.scanner import scan_directory
        scan = scan_directory(input_dir, recursive=self.chk_recursive.isChecked())
        self.perf_monitor.start(scan.image_count)

        self.worker = CompressWorker(
            input_dir=input_dir,
            output_dir=output_dir,
            fmt=fmt,
            params=self._get_params(),
            overwrite=overwrite,
            recursive=self.chk_recursive.isChecked(),
            max_workers=self.workers_spin.value(),
            conflict_strategy=conflict,
            max_retries=1,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, current, total, msg, speed):
        self.progress_widget.update_progress(current, total, msg)
        self.perf_monitor.update_progress(current, speed)
        if hasattr(self.progress_widget, 'set_speed'):
            self.progress_widget.set_speed(speed)

    def _on_finished(self, stats: BatchStats):
        self.run_btn.setEnabled(True)
        self.perf_monitor.stop()

        self.progress_widget.set_complete(
            f"完成: {stats.compressed_files}/{stats.total_files} 已压缩"
            + (f" ({stats.skipped_files} 跳过)" if stats.skipped_files else "")
            + (f" ({stats.failed_files} 失败)" if stats.failed_files else "")
        )
        self.progress_widget.set_stats(
            f"原始: {stats.original_size_mb:.1f} MB → "
            f"压缩后: {stats.compressed_size_mb:.1f} MB "
            f"(节省 {stats.saved_percent:.1f}%)"
        )
        self.config.last_output_dir = stats.output_dir
        self._last_stats = stats
        self.preview_btn.setEnabled(bool(stats.results))

        # 自动保存压缩历史
        try:
            from engine.history import save_history_entry
            save_history_entry(
                stats=stats,
                format_name=self.format_combo.currentText().lower(),
                quality=self._get_params().quality,
                input_dir=self.input_edit.text(),
            )
        except Exception:
            pass

        if stats.errors:
            QMessageBox.warning(self, "部分文件失败",
                f"{stats.failed_files} 个文件压缩失败:\n" +
                "\n".join(stats.errors[:10]))

    def _show_preview(self):
        if self._last_stats and self._last_stats.results:
            from ui.preview_dialog import PreviewDialog
            PreviewDialog.show_results(self._last_stats.results, parent=self)

    def _on_error(self, msg):
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, "压缩失败", msg)

    def set_input_dir(self, path: str):
        self.input_edit.setText(path)

    def get_output_dir(self) -> str:
        if self.mode_overwrite.isChecked():
            return self.input_edit.text().strip()
        return self.output_edit.text().strip()
