"""
准备页 Tab — 重命名 + 清除 EXIF
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QCheckBox,
    QFileDialog, QGroupBox, QMessageBox,
)
from PySide6.QtCore import QThread, Signal, Qt

from core.prepare import prepare_files, ScanResult
from engine.scanner import scan_directory
from ui.widgets.card_group import create_card_group


class PrepareWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, input_dir, output_dir, rename_images, rename_videos,
                 strip_exif, overwrite, recursive=False):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.rename_images = rename_images
        self.rename_videos = rename_videos
        self.strip_exif = strip_exif
        self.overwrite = overwrite
        self.recursive = recursive

    def run(self):
        try:
            scan_result = scan_directory(self.input_dir, recursive=self.recursive)
            result = prepare_files(
                scan_result,
                output_dir=self.output_dir,
                rename_images=self.rename_images,
                rename_videos=self.rename_videos,
                do_strip_exif=self.strip_exif,
                overwrite=self.overwrite,
                progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class PrepareTab(QWidget):
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
        self.input_edit.setPlaceholderText("选择或拖拽图片文件夹...")
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(70)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_input)
        ig.addWidget(self.input_edit, 1)
        ig.addWidget(browse_btn)
        layout.addLayout(create_card_group("输入目录", ig))

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
        self.output_edit.setPlaceholderText("输出目录路径...")
        self.output_browse = QPushButton("浏览")
        self.output_browse.setFixedWidth(70)
        self.output_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.output_browse.clicked.connect(self._browse_output)
        dir_row.addWidget(self.output_edit, 1)
        dir_row.addWidget(self.output_browse)
        og.addLayout(dir_row)
        layout.addLayout(create_card_group("输出设置", og))

        # ── 处理选项 ──
        oo = QVBoxLayout()
        oo.setSpacing(2)
        self.chk_rename_images = QCheckBox("重命名图片  (0001, 0002, ...)")
        self.chk_rename_images.setChecked(True)
        self.chk_rename_videos = QCheckBox("重命名视频  (video001, video002, ...)")
        self.chk_rename_videos.setChecked(True)
        self.chk_strip_exif = QCheckBox("清除 EXIF 元数据")
        self.chk_strip_exif.setChecked(True)
        self.chk_recursive = QCheckBox("递归扫描子目录")
        self.chk_recursive.setToolTip("递归处理子文件夹中的图片")
        oo.addWidget(self.chk_rename_images)
        oo.addWidget(self.chk_rename_videos)
        oo.addWidget(self.chk_strip_exif)
        oo.addWidget(self.chk_recursive)
        layout.addLayout(create_card_group("处理选项", oo))

        # ── 扫描信息 ──
        self.scan_label = QLabel("")
        self.scan_label.setObjectName("secondaryLabel")
        layout.addWidget(self.scan_label)

        # ── 操作按钮 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.scan_btn = QPushButton("扫描")
        self.scan_btn.setFixedWidth(80)
        self.scan_btn.setToolTip("扫描目录预览文件")
        self.scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_btn.clicked.connect(self._scan)
        self.run_btn = QPushButton("开始处理")
        self.run_btn.setObjectName("actionBtn")
        self.run_btn.setFixedWidth(120)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._run)
        btn_row.addWidget(self.scan_btn)
        btn_row.addWidget(self.run_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

    def _browse_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if path:
            self.input_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_edit.setText(path)

    def _on_mode_changed(self, checked):
        is_new = self.mode_new.isChecked()
        self.output_edit.setEnabled(is_new)
        self.output_browse.setEnabled(is_new)

    def _scan(self):
        input_dir = self.input_edit.text().strip()
        if not input_dir:
            QMessageBox.warning(self, "提示", "请先选择输入目录")
            return
        try:
            recursive = self.chk_recursive.isChecked()
            result = scan_directory(input_dir, recursive=recursive)
            info_parts = [
                f"扫描结果: {result.image_count} 张图片",
                f"{result.video_count} 个视频",
                f"共 {result.total_size_mb:.1f} MB",
            ]
            if result.subdirs > 0:
                info_parts.append(f"{result.subdirs} 个子目录")
            self.scan_label.setText(" · ".join(info_parts))
        except Exception as e:
            QMessageBox.critical(self, "扫描失败", str(e))

    def _run(self):
        if self.worker and self.worker.isRunning():
            return  # 防双击
        input_dir = self.input_edit.text().strip()
        if not input_dir:
            QMessageBox.warning(self, "提示", "请先选择输入目录")
            return

        overwrite = self.mode_overwrite.isChecked()
        output_dir = input_dir if overwrite else self.output_edit.text().strip()

        if not overwrite and not output_dir:
            from pathlib import Path
            p = Path(input_dir)
            output_dir = str(p.parent / f"{p.name}_ready")
            self.output_edit.setText(output_dir)

        self.run_btn.setEnabled(False)
        self.progress_widget.reset()

        self.worker = PrepareWorker(
            input_dir=input_dir,
            output_dir=output_dir,
            rename_images=self.chk_rename_images.isChecked(),
            rename_videos=self.chk_rename_videos.isChecked(),
            strip_exif=self.chk_strip_exif.isChecked(),
            overwrite=overwrite,
            recursive=self.chk_recursive.isChecked(),
        )
        self.worker.progress.connect(self.progress_widget.update_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, result):
        self.run_btn.setEnabled(True)
        self.progress_widget.set_complete(
            f"完成: {result.renamed_images} 张图片重命名 · "
            f"{result.renamed_videos} 个视频重命名 · "
            f"{result.exif_stripped} 个 EXIF 已清除"
        )
        self.config.last_output_dir = result.output_dir

    def _on_error(self, msg):
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, "处理失败", msg)

    def get_output_dir(self) -> str:
        if self.mode_overwrite.isChecked():
            return self.input_edit.text().strip()
        return self.output_edit.text().strip()
