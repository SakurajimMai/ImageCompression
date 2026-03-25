"""
预览对比弹窗 — 压缩前后并排预览 + 放大镜 + 文件大小柱状图
"""
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSplitter, QScrollArea, QWidget, QComboBox, QGroupBox,
)
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QImage
from engine.formats.base import CompressResult


def _load_pixmap(path: Path) -> QPixmap:
    """加载图片为 QPixmap，支持 AVIF 等 Qt 不原生支持的格式"""
    pixmap = QPixmap(str(path))
    if not pixmap.isNull():
        return pixmap
    # Qt 无法加载时，回退使用 Pillow（支持 AVIF/HEIC 等）
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        data = img.tobytes("raw", "RGB")
        qimg = QImage(data, img.width, img.height,
                       3 * img.width, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg)
    except Exception:
        return pixmap  # 返回空 pixmap


class ZoomLabel(QLabel):
    """支持放大镜效果的图片标签"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._zoom_factor = 3
        self._zoom_size = 120
        self._mouse_pos = None
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_image(self, pixmap: QPixmap):
        self._pixmap = pixmap
        scaled = pixmap.scaled(
            self.width(), self.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmap:
            self.set_image(self._pixmap)

    def mouseMoveEvent(self, event):
        self._mouse_pos = event.pos()
        self.update()

    def leaveEvent(self, event):
        self._mouse_pos = None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._mouse_pos is None or self._pixmap is None or self.pixmap() is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 计算显示区域
        displayed = self.pixmap()
        if displayed is None:
            painter.end()
            return

        # 图像偏移（居中显示）
        offset_x = (self.width() - displayed.width()) // 2
        offset_y = (self.height() - displayed.height()) // 2

        # 鼠标在图片上的相对位置
        rel_x = self._mouse_pos.x() - offset_x
        rel_y = self._mouse_pos.y() - offset_y

        if 0 <= rel_x < displayed.width() and 0 <= rel_y < displayed.height():
            # 计算原图对应区域
            scale_x = self._pixmap.width() / displayed.width()
            scale_y = self._pixmap.height() / displayed.height()

            src_x = int(rel_x * scale_x)
            src_y = int(rel_y * scale_y)

            half_zoom = self._zoom_size // (self._zoom_factor * 2)
            sx = max(0, src_x - half_zoom)
            sy = max(0, src_y - half_zoom)
            sw = min(self._pixmap.width() - sx, half_zoom * 2)
            sh = min(self._pixmap.height() - sy, half_zoom * 2)

            # 裁切并放大
            cropped = self._pixmap.copy(sx, sy, sw, sh)
            zoomed = cropped.scaled(
                self._zoom_size, self._zoom_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            # 绘制放大镜
            mx = self._mouse_pos.x() + 20
            my = self._mouse_pos.y() - self._zoom_size - 10

            # 确保在窗口内
            if mx + self._zoom_size > self.width():
                mx = self._mouse_pos.x() - self._zoom_size - 20
            if my < 0:
                my = self._mouse_pos.y() + 20

            # 黑色边框
            painter.setPen(QPen(QColor(30, 30, 30), 2))
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRect(mx - 2, my - 2, self._zoom_size + 4, self._zoom_size + 4)

            painter.drawPixmap(mx, my, zoomed)

        painter.end()


class SizeBarWidget(QWidget):
    """文件大小柱状图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_size = 0
        self._compressed_size = 0
        self.setFixedHeight(60)

    def set_sizes(self, original: int, compressed: int):
        self._original_size = original
        self._compressed_size = compressed
        self.update()

    def paintEvent(self, event):
        if self._original_size <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width() - 20
        h = self.height()
        bar_h = 16
        gap = 6

        # 原始大小条
        y1 = h // 2 - bar_h - gap // 2
        painter.setBrush(QColor(239, 68, 68))   # red
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(10, y1, w, bar_h, 4, 4)

        # 压缩后大小条
        y2 = h // 2 + gap // 2
        ratio = self._compressed_size / self._original_size if self._original_size > 0 else 0
        bar_w = max(4, int(w * ratio))
        painter.setBrush(QColor(34, 197, 94))    # green
        painter.drawRoundedRect(10, y2, bar_w, bar_h, 4, 4)

        # 标签
        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))

        orig_mb = self._original_size / (1024 * 1024)
        comp_mb = self._compressed_size / (1024 * 1024)
        saved = (1 - ratio) * 100

        painter.drawText(14, y1 + bar_h - 3, f"原始: {orig_mb:.2f} MB")
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(14, y2 + bar_h - 3, f"压缩: {comp_mb:.2f} MB (节省 {saved:.0f}%)")

        painter.end()


class PreviewDialog(QDialog):
    """预览对比弹窗"""

    def __init__(self, results: list[CompressResult] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("压缩预览对比")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)
        self.results = results or []
        self._current_index = 0
        self._setup_ui()

        if self.results:
            self._load_result(0)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # ── 文件选择 ──
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("选择文件:"))
        self.file_combo = QComboBox()
        self.file_combo.setMinimumWidth(300)
        for r in self.results:
            name = Path(r.input_path).name
            status = "✓" if r.success else "✗"
            self.file_combo.addItem(f"{status} {name}")
        self.file_combo.currentIndexChanged.connect(self._load_result)
        top_row.addWidget(self.file_combo, 1)

        self.prev_btn = QPushButton("◀ 上一张")
        self.prev_btn.clicked.connect(lambda: self._navigate(-1))
        self.next_btn = QPushButton("下一张 ▶")
        self.next_btn.clicked.connect(lambda: self._navigate(1))
        top_row.addWidget(self.prev_btn)
        top_row.addWidget(self.next_btn)
        layout.addLayout(top_row)

        # ── 图片对比 ──
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 原图
        orig_group = QGroupBox("原始图片")
        orig_l = QVBoxLayout(orig_group)
        orig_l.setContentsMargins(4, 4, 4, 4)
        self.orig_label = ZoomLabel()
        self.orig_label.setMinimumSize(300, 300)
        orig_l.addWidget(self.orig_label)
        self.orig_info = QLabel()
        self.orig_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orig_l.addWidget(self.orig_info)
        splitter.addWidget(orig_group)

        # 压缩后
        comp_group = QGroupBox("压缩后")
        comp_l = QVBoxLayout(comp_group)
        comp_l.setContentsMargins(4, 4, 4, 4)
        self.comp_label = ZoomLabel()
        self.comp_label.setMinimumSize(300, 300)
        comp_l.addWidget(self.comp_label)
        self.comp_info = QLabel()
        self.comp_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_l.addWidget(self.comp_info)
        splitter.addWidget(comp_group)

        layout.addWidget(splitter, 1)

        # ── 大小柱状图 ──
        self.size_bar = SizeBarWidget()
        layout.addWidget(self.size_bar)

        # ── 底部按钮 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _navigate(self, delta: int):
        new_index = self._current_index + delta
        if 0 <= new_index < len(self.results):
            self.file_combo.setCurrentIndex(new_index)

    def _load_result(self, index: int):
        if index < 0 or index >= len(self.results):
            return

        self._current_index = index
        result = self.results[index]

        # 更新导航按钮
        self.prev_btn.setEnabled(index > 0)
        self.next_btn.setEnabled(index < len(self.results) - 1)

        # 加载原图
        orig_path = Path(result.input_path)
        if orig_path.exists():
            pixmap = _load_pixmap(orig_path)
            self.orig_label.set_image(pixmap)
            orig_mb = result.original_size / (1024 * 1024)
            self.orig_info.setText(
                f"{orig_path.name} · {pixmap.width()}×{pixmap.height()} · {orig_mb:.2f} MB"
            )
        else:
            self.orig_label.setText("原始文件已不存在")
            self.orig_info.setText("")

        # 加载压缩后
        if result.success:
            comp_path = Path(result.output_path)
            if comp_path.exists():
                pixmap = _load_pixmap(comp_path)
                self.comp_label.set_image(pixmap)
                comp_mb = result.compressed_size / (1024 * 1024)
                saved = result.saved_percent
                self.comp_info.setText(
                    f"{comp_path.name} · {pixmap.width()}×{pixmap.height()} · "
                    f"{comp_mb:.2f} MB (节省 {saved:.0f}%)"
                )
            else:
                self.comp_label.setText("压缩文件已不存在")
                self.comp_info.setText("")
        else:
            self.comp_label.setText(f"压缩失败: {result.error}")
            self.comp_info.setText("")

        # 更新柱状图
        self.size_bar.set_sizes(result.original_size, result.compressed_size)

    @staticmethod
    def show_results(results: list[CompressResult], parent=None):
        """便捷方法：显示压缩结果预览"""
        dialog = PreviewDialog(results=results, parent=parent)
        dialog.exec()
